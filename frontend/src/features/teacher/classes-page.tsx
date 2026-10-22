"use client";

import { useCallback, useState } from "react";
import { AssignmentPicker } from "@/features/teacher/assignment-picker";
import { Card, DataState, PageHeader, Table, Td } from "@/components/ui";
import { useApiQuery } from "@/lib/api/query";
import { teacherApi, type Assignment } from "@/services/teacher";

export function TeacherClassesPage() {
  const [a, setA] = useState<Assignment | null>(null);
  const onChange = useCallback((x: Assignment) => setA(x), []);
  const students = useApiQuery(a ? teacherApi.sectionStudents(a.section_id) : null);
  return (
    <>
      <PageHeader title="Assigned classes and subjects" description="You can only view students in classes you are assigned to." />
      <div className="space-y-5">
        <AssignmentPicker value={a} onChange={onChange} />
        {a && (
          <Card title={`Class ${a.section} · ${a.subject}`} padded={false}>
            <DataState state={students}>
              {(list) => (
                <Table headers={["Roll", "Student ID", "Name"]} caption="Class roster">
                  {list.map((s) => (
                    <tr key={s.student_id}>
                      <Td>{s.roll_no}</Td>
                      <Td>{s.student_code}</Td>
                      <Td className="font-medium">{s.name}</Td>
                    </tr>
                  ))}
                </Table>
              )}
            </DataState>
          </Card>
        )}
      </div>
    </>
  );
}
