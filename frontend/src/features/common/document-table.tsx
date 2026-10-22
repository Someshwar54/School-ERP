import { Badge, Table, Td } from "@/components/ui";
import { formatDate, titleCase } from "@/lib/format";
import type { DocumentRecord } from "@/services/shared";

/** Document metadata list. File storage is not connected, so files show as "Not connected". */
export function DocumentTable({ documents }: { documents: DocumentRecord[] }) {
  return (
    <Table headers={["Title", "Category", "Scope", "Added", "File"]} empty={documents.length === 0} caption="Documents">
      {documents.map((d) => (
        <tr key={d.id}>
          <Td className="font-medium">{d.title}</Td>
          <Td>{titleCase(d.category)}</Td>
          <Td>{d.scope}</Td>
          <Td>{formatDate(d.created_at)}</Td>
          <Td>{d.available ? "Available" : <Badge>Not connected</Badge>}</Td>
        </tr>
      ))}
    </Table>
  );
}
