package com.example.activitytracker;

import android.content.res.Configuration;
import android.graphics.Color;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import com.google.firebase.database.DataSnapshot;
import com.google.firebase.database.DatabaseError;
import com.google.firebase.database.DatabaseReference;
import com.google.firebase.database.FirebaseDatabase;
import com.google.firebase.database.ValueEventListener;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class MainActivity extends AppCompatActivity {
    private TextView textActivity, textConfidence, textTimestamp;
    private HistoryAdapter historyAdapter;
    private List<Map<String, String>> historyList;
    private DatabaseReference currentRef, historyRef;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        textActivity = findViewById(R.id.text_activity);
        textConfidence = findViewById(R.id.text_confidence);
        textTimestamp = findViewById(R.id.text_timestamp);
        Button btnDeleteHistory = findViewById(R.id.btnDeleteHistory);
        RecyclerView recyclerHistory = findViewById(R.id.recycler_history);

        textActivity.setText("Syncing...");
        textConfidence.setText("Confidence: --");
        textTimestamp.setText("Connecting...");

        if (recyclerHistory != null) {
            recyclerHistory.setLayoutManager(new LinearLayoutManager(this));
            historyList = new ArrayList<>();
            historyAdapter = new HistoryAdapter(historyList);
            recyclerHistory.setAdapter(historyAdapter);
        }

        FirebaseDatabase database = FirebaseDatabase.getInstance("https://wearable-activity-tracke-a5c56-default-rtdb.firebaseio.com/");
        currentRef = database.getReference("current_reading");
        historyRef = database.getReference("history");

        currentRef.addValueEventListener(new ValueEventListener() {
            @Override
            public void onDataChange(@NonNull DataSnapshot snapshot) {
                if (isFinishing() || isDestroyed() || !snapshot.exists()) return;

                String activity = snapshot.child("activity").getValue(String.class);
                if (activity == null || activity.trim().isEmpty()) activity = "Stationary";

                Object rawConf = snapshot.child("confidence").getValue();
                double confidenceValue = (rawConf instanceof Number) ? ((Number) rawConf).doubleValue() : 0.0;
                String timestamp = snapshot.child("timestamp").getValue(String.class);

                final String fActivity = activity;
                final double fConfidence = confidenceValue;
                final String fTimestamp = (timestamp != null) ? timestamp : "---";

                runOnUiThread(() -> updateCurrentUI(fActivity, fConfidence, fTimestamp));
            }
            @Override public void onCancelled(@NonNull DatabaseError error) {}
        });

        historyRef.addValueEventListener(new ValueEventListener() {
            @Override
            public void onDataChange(@NonNull DataSnapshot snapshot) {
                if (isFinishing() || isDestroyed()) return;
                historyList.clear();
                for (DataSnapshot recordSnapshot : snapshot.getChildren()) {
                    String act = recordSnapshot.child("activity").getValue(String.class);
                    String time = recordSnapshot.child("timestamp").getValue(String.class);
                    Map<String, String> record = new HashMap<>();
                    record.put("activity", (act == null) ? "Stationary" : act);
                    record.put("timestamp", (time == null) ? "--" : time);
                    historyList.add(record);
                }
                runOnUiThread(() -> {
                    Collections.reverse(historyList);
                    historyAdapter.notifyDataSetChanged();
                });
            }
            @Override public void onCancelled(@NonNull DatabaseError error) {}
        });

        if (btnDeleteHistory != null) {
            btnDeleteHistory.setOnClickListener(v -> {
                AlertDialog dialog = new AlertDialog.Builder(this)
                        .setTitle("Clear History")
                        .setMessage("This will permanently delete all records. Continue?")
                        .setPositiveButton("Delete", (d, which) -> historyRef.removeValue())
                        .setNegativeButton("Cancel", null)
                        .create();

                dialog.show();

                dialog.getButton(AlertDialog.BUTTON_POSITIVE).setTextColor(Color.parseColor("#E53935"));

                int nightModeFlags = getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK;
                if (nightModeFlags == Configuration.UI_MODE_NIGHT_YES) {
                    dialog.getButton(AlertDialog.BUTTON_NEGATIVE).setTextColor(Color.WHITE);
                } else {
                    dialog.getButton(AlertDialog.BUTTON_NEGATIVE).setTextColor(Color.DKGRAY);
                }
            });
        }
    }

    private void updateCurrentUI(String activity, double confidence, String timestamp) {
        if (textActivity == null || isFinishing() || isDestroyed()) return;

        textActivity.setText(activity);
        textConfidence.setText(String.format("AI Confidence: %.2f%%", confidence));
        textTimestamp.setText("Last updated: " + timestamp);

        int nightModeFlags = getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK;

        if ("Running".equalsIgnoreCase(activity)) {
            textActivity.setTextColor(Color.parseColor("#E53935"));
        } else if ("Walking".equalsIgnoreCase(activity)) {
            textActivity.setTextColor(Color.parseColor("#FFC107"));
        } else {
            if (nightModeFlags == Configuration.UI_MODE_NIGHT_YES) {
                textActivity.setTextColor(Color.WHITE);
            } else {
                textActivity.setTextColor(Color.BLACK);
            }
        }
    }
}