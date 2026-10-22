"use client";

import { useEffect } from "react";
import { DataState, EmptyState, Field, Select } from "@/components/ui";
import { useApiQuery } from "@/lib/api/query";
import { teacherApi, type Assignment } from "@/services/teacher";

export const assignmentKey = (a: Pick<Assignment, "section_id" | "subject_id">) => `${a.section_id}:${a.subject_id}`;

/** Lists only the class/subject pairs the backend says this teacher is assigned to. */
export function AssignmentPicker({ value, onChange }: { value: Assignment | null; onChange: (a: Assignment) => void }) {
  const state = useApiQuery(teacherApi.assignments());
  const list = state.data;
  useEffect(() => {
    if (list && list.length && !value) onChange(list[0]);
  }, [list, value, onChange]);
  return (
    <DataState state={state}>
      {(items) =>
        items.length === 0 ? (
          <EmptyState title="No teaching assignments" text="Ask the school office to assign classes to your account." />
        ) : (
          <div className="max-w-sm">
            <Field label="Class and subject">
              {(p) => (
                <Select
                  value={value ? assignmentKey(value) : ""}
                  onChange={(e) => {
                    const a = items.find((i) => assignmentKey(i) === e.target.value);
                    if (a) onChange(a);
                  }}
                  {...p}
                >
                  {items.map((a) => (
                    <option key={assignmentKey(a)} value={assignmentKey(a)}>
                      Class {a.section} · {a.subject}
                    </option>
                  ))}
                </Select>
              )}
            </Field>
          </div>
        )
      }
    </DataState>
  );
}
