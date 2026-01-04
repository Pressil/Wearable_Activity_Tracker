package com.example.activitytracker;

import android.content.res.ColorStateList;
import android.graphics.Color;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import java.util.List;
import java.util.Map;

public class HistoryAdapter extends RecyclerView.Adapter<HistoryAdapter.ViewHolder> {

    private List<Map<String, String>> historyList;

    public HistoryAdapter(List<Map<String, String>> historyList) {
        this.historyList = historyList;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        // Inflates the modern layout we designed
        View view = LayoutInflater.from(parent.getContext())
                .inflate(R.layout.item_history, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        Map<String, String> record = historyList.get(position);

        String activity = record.get("activity");
        String time = record.get("timestamp");

        // FIX: Default to Stationary in the list view
        String displayLabel = (activity == null || activity.trim().isEmpty() || "Stationary".equalsIgnoreCase(activity))
                ? "Stationary" : activity;

        holder.activityText.setText(displayLabel);
        holder.timeText.setText(time != null ? time : "--:--");

        if ("Running".equalsIgnoreCase(displayLabel)) {
            holder.indicator.setBackgroundTintList(ColorStateList.valueOf(Color.RED));
        } else if ("Walking".equalsIgnoreCase(displayLabel)) {
            holder.indicator.setBackgroundTintList(ColorStateList.valueOf(Color.parseColor("#FFA500")));
        } else {
            // Stationary gets a Gray indicator
            holder.indicator.setBackgroundTintList(ColorStateList.valueOf(Color.GRAY));
        }
    }

    @Override
    public int getItemCount() {
        return historyList.size();
    }

    public static class ViewHolder extends RecyclerView.ViewHolder {
        public TextView activityText, timeText;
        public View indicator; // The status circle

        public ViewHolder(View itemView) {
            super(itemView);
            activityText = itemView.findViewById(R.id.history_activity);
            timeText = itemView.findViewById(R.id.history_timestamp); // Matches modern XML ID
            indicator = itemView.findViewById(R.id.activity_indicator); // Link to the circle in XML
        }
    }
}