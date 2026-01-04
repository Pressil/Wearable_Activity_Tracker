#include <rtthread.h>
#include <rtdevice.h>
#include <board.h>
#include <stdlib.h>
#include <string.h>
#include <drv_spi.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <arpa/inet.h>
#include <netdev.h>
#include "icm20608.h"
#include "spi_wifi_rw007.h"

#define WIFI_SSID        "GlobeAtHome_8DE90_2.4"
#define WIFI_PASSWORD    "tP3zcaMP1"
#define SERVER_IP        "192.168.254.144"
#define SERVER_PORT      5000
#define WINDOW_SIZE      50

/* --- NOISE REDUCTION SETTINGS --- */
#define FILTER_ALPHA     0.2f   // Smoothing factor
#define NOISE_THRESHOLD  150    // Dead-zone threshold

static char json_payload[3500];
static char http_header[300];

// Filter states
static float last_ax = 0, last_ay = 0, last_az = 0;
static float last_gx = 0, last_gy = 0, last_gz = 0;

/* Helper to apply filtering and noise gate */
rt_int16_t apply_filter(float *last_val, rt_int16_t new_val) {
    *last_val = (FILTER_ALPHA * new_val) + ((1.0f - FILTER_ALPHA) * (*last_val));
    if (abs((int)*last_val) < NOISE_THRESHOLD) return 0;
    return (rt_int16_t)*last_val;
}

static void ml_wireless_thread_entry(void *parameter)
{
    icm20608_device_t dev = icm20608_init("i2c2");
    if (!dev) return;

    rt_int16_t raw_ax, raw_ay, raw_az, raw_gx, raw_gy, raw_gz;
    rt_int16_t f_ax, f_ay, f_az, f_gx, f_gy, f_gz;

    while (1)
    {
        // 1. Collect and Filter Data
        rt_memset(json_payload, 0, sizeof(json_payload));
        int pos = 0;
        pos += rt_snprintf(json_payload + pos, sizeof(json_payload) - pos, "{\"readings\":[");

        for (int i = 0; i < WINDOW_SIZE; i++)
        {
            icm20608_get_accel(dev, &raw_ax, &raw_ay, &raw_az);
            icm20608_get_gyro(dev, &raw_gx, &raw_gy, &raw_gz);

            f_ax = apply_filter(&last_ax, raw_ax);
            f_ay = apply_filter(&last_ay, raw_ay);
            f_az = apply_filter(&last_az, raw_az);
            f_gx = apply_filter(&last_gx, raw_gx);
            f_gy = apply_filter(&last_gy, raw_gy);
            f_gz = apply_filter(&last_gz, raw_gz);

            if (pos < (sizeof(json_payload) - 120)) {
                pos += rt_snprintf(json_payload + pos, sizeof(json_payload) - pos,
                           "{\"ax\":%d,\"ay\":%d,\"az\":%d,\"gx\":%d,\"gy\":%d,\"gz\":%d}%s",
                           f_ax, f_ay, f_az, f_gx, f_gy, f_gz, (i == WINDOW_SIZE - 1) ? "" : ",");
            }
            rt_thread_mdelay(20);
        }
        pos += rt_snprintf(json_payload + pos, sizeof(json_payload) - pos, "]}");

        // 2. Networking logic with Connection Check
        if (rt_wlan_is_connected())
        {
            int sock = socket(AF_INET, SOCK_STREAM, 0);
            if (sock >= 0)
            {
                struct sockaddr_in server_addr;
                rt_memset(&server_addr, 0, sizeof(server_addr));
                server_addr.sin_family = AF_INET;
                server_addr.sin_port = htons(SERVER_PORT);
                server_addr.sin_addr.s_addr = inet_addr(SERVER_IP);

                struct timeval timeout = {2, 0};
                setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, (const char*)&timeout, sizeof(timeout));

                if (connect(sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) >= 0) {
                    int body_len = strlen(json_payload);
                    int head_len = rt_snprintf(http_header, sizeof(http_header),
                                   "POST /readings HTTP/1.1\r\n"
                                   "Host: %s\r\n"
                                   "Content-Type: application/json\r\n"
                                   "Content-Length: %d\r\n"
                                   "Connection: close\r\n\r\n", SERVER_IP, body_len);

                    send(sock, http_header, head_len, 0);
                    send(sock, json_payload, body_len, 0);
                    rt_kprintf("[OK] Sent %d bytes\n", body_len);
                } else {
                    rt_kprintf("[FAIL] Server connection error at %s\n", SERVER_IP);
                }
                closesocket(sock);
            }
        } else {
            rt_kprintf("[WLAN] Not connected, skipping send...\n");
        }
        rt_thread_mdelay(1000);
    }
}

int main(void)
{
    // Initialize Hardware
    rt_hw_spi_device_attach("spi2", "spi20", GET_PIN(B, 12), RT_NULL);
    rt_thread_mdelay(200);

    // Initialize Network
#ifdef RT_USING_WLAN
    rt_kprintf("Connecting to WiFi: %s...\n", WIFI_SSID);
    rt_wlan_connect(WIFI_SSID, WIFI_PASSWORD);

    // Wait for IP (Avoid connection error on boot)
    int timeout = 0;
    while (!rt_wlan_is_connected() && timeout < 20) {
        rt_thread_mdelay(500);
        timeout++;
    }
    rt_thread_mdelay(2000); // Stabilization delay
#endif

    // Start App Thread
    rt_thread_t tid = rt_thread_create("wifi_ai", ml_wireless_thread_entry, RT_NULL, 4096, 25, 10);
    if (tid) rt_thread_startup(tid);

    return RT_EOK;
}
