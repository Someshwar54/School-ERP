import { Clock, Mail, MapPin, Phone } from "lucide-react";
import { EnquiryForm } from "@/features/site/enquiry-form";
import { PageHero, Section } from "@/features/site/section";
import { school } from "@/config/school";

export function ContactPage() {
  const c = school.contact;
  return (
    <>
      <PageHero
        eyebrow="Get in touch"
        title="Contact us"
        intro="Questions about admissions or the school? Send us an enquiry or visit the office."
      />
      <Section>
        <div className="grid gap-10 lg:grid-cols-[1fr_1.4fr]">
          <address className="space-y-5 not-italic">
            {[
              { icon: MapPin, label: "Address", value: c.addressLines.join(", ") },
              { icon: Phone, label: "Phone", value: c.phone },
              { icon: Mail, label: "Email", value: c.email },
              { icon: Clock, label: "Office hours", value: c.officeHours },
            ].map(({ icon: Icon, label, value }) => (
              <div key={label} className="flex gap-3">
                <span className="inline-flex size-10 shrink-0 items-center justify-center rounded-brand bg-brand-soft text-brand">
                  <Icon className="size-5" aria-hidden />
                </span>
                <div>
                  <p className="text-sm font-semibold">{label}</p>
                  <p className="text-sm text-muted">{value}</p>
                </div>
              </div>
            ))}
          </address>
          <div className="rounded-brand border border-line p-6">
            <h2 className="font-display text-xl font-semibold">Admission enquiry</h2>
            <p className="mt-1 text-sm text-muted">We use these details only to respond to your enquiry.</p>
            <div className="mt-5">
              <EnquiryForm />
            </div>
          </div>
        </div>
      </Section>
    </>
  );
}
