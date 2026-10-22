"use client";

import { TimetableView } from "@/features/common/timetable-grid";
import { useApiQuery } from "@/lib/api/query";
import { studentApi } from "@/services/student";

export function StudentTimetablePage() {
  return (
    <TimetableView
      state={useApiQuery(studentApi.timetable())}
      show="teacher"
      title="Timetable"
      description="Your weekly class schedule. Today's column is highlighted."
    />
  );
}
