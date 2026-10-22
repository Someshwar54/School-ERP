/** Unauthenticated endpoints used by the public website. */
import { http } from "@/lib/api/client";

export interface EnquiryInput {
  parent_name: string;
  email: string;
  phone: string;
  grade_sought: string;
  message?: string;
  website?: string;
}

export const publicApi = {
  createEnquiry: (body: EnquiryInput) => http.post<{ ok: boolean; message: string; notifications?: string }>("/public/enquiries", body),
};
