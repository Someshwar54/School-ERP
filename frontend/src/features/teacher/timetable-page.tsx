"use client";

import { TimetableView } from "@/features/common/timetable-grid";
import { useApiQuery } from "@/lib/api/query";
import { teacherApi } from "@/services/teacher";

export function TeacherTimetablePage() {
  return (
    <TimetableView
      state={useApiQuery(teacherApi.timetable())}
      show="section"
      title="My timetable"
      description="Your teaching periods for the week."
    />
  );
}
