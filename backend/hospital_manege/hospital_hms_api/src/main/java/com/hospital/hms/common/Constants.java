package com.hospital.hms.common;

import java.util.AbstractMap;
import java.util.Map;

public class Constants {

    public static final String WORK_PLAN_SCHEDULE_KEY = "work_plan_schedule_";

    public static final Map<String, String> APPOINTMENT_SLOT = Map.ofEntries(
            new AbstractMap.SimpleEntry<>("1", "08:00"),
            new AbstractMap.SimpleEntry<>("2", "08:30"),
            new AbstractMap.SimpleEntry<>("3", "09:00"),
            new AbstractMap.SimpleEntry<>("4", "09:30"),
            new AbstractMap.SimpleEntry<>("5", "10:00"),
            new AbstractMap.SimpleEntry<>("6", "10:30"),
            new AbstractMap.SimpleEntry<>("7", "11:00"),
            new AbstractMap.SimpleEntry<>("8", "11:30"),
            new AbstractMap.SimpleEntry<>("9", "13:00"),
            new AbstractMap.SimpleEntry<>("10", "13:30"),
            new AbstractMap.SimpleEntry<>("11", "14:00"),
            new AbstractMap.SimpleEntry<>("12", "14:30"),
            new AbstractMap.SimpleEntry<>("13", "15:00"),
            new AbstractMap.SimpleEntry<>("14", "15:30"),
            new AbstractMap.SimpleEntry<>("15", "16:00")
    );;

}
