import type { SchoolConfig } from "../schema";

/** Fictional demonstration school. Replace with a school's approved content. */
export const demoSchool: SchoolConfig = {
  slug: "demo",
  name: "Sunrise Valley Public School",
  shortName: "Sunrise Valley",
  tagline: "Curious minds. Kind hearts. Confident futures.",
  affiliation: "Co-educational day school, Grades 6–10 (fictional demonstration school)",
  established: 1998,
  isFictional: true,
  logo: { src: "/schools/demo/logo.svg", alt: "Sunrise Valley Public School crest" },
  favicon: "/schools/demo/logo.svg",
  theme: {
    primary: "#1f4e79",
    primaryContrast: "#ffffff",
    secondary: "#c8761d",
    surface: "#f7f5f0",
    radius: "md",
    chart: ["#2a6db0", "#c8761d"],
  },
  regional: { locale: "en-IN", currency: "INR", timezone: "Asia/Kolkata" },
  terminology: { student: "Student", staff: "Staff", director: "Director", portal: "ERP Portal" },
  contact: {
    addressLines: ["12 Lakeview Road, Fictional Nagar", "Demo City 400000, India"],
    phone: "+91 00000 00000",
    email: "office@sunrisevalley.school.example",
    officeHours: "Monday to Saturday, 8:00 am – 3:00 pm (closed second Saturdays)",
  },
  content: {
    hero: {
      eyebrow: "Admissions open for 2027–28",
      title: "A school where every learner is known, challenged and supported",
      subtitle:
        "Sunrise Valley Public School offers a balanced education for Grades 6 to 10, combining strong academics with sport, arts and service.",
    },
    stats: [
      { label: "Students", value: "300" },
      { label: "Teachers", value: "14" },
      { label: "Student–teacher ratio", value: "21:1" },
      { label: "Years of learning", value: "28" },
    ],
    highlights: [
      { icon: "book", title: "Strong foundations", text: "A structured curriculum with regular, transparent assessment." },
      { icon: "flask", title: "Hands-on science", text: "Practical work in well-equipped laboratories from Grade 6." },
      { icon: "trophy", title: "Sport and wellbeing", text: "Daily physical education, inter-house sport and counselling support." },
      { icon: "palette", title: "Arts and clubs", text: "Music, art, debate and coding clubs every week." },
    ],
    about: {
      intro:
        "Founded in 1998, Sunrise Valley Public School is a co-educational day school serving families across Demo City. We believe that good schooling is built on clear expectations, caring relationships and steady, honest feedback.",
      vision: "To help every student grow into a thoughtful, capable and compassionate member of society.",
      mission: [
        "Teach a broad, rigorous curriculum with attention to each learner's progress.",
        "Build character through responsibility, service and respect for others.",
        "Work in partnership with families through open, timely communication.",
      ],
      principalMessage: {
        name: "Dr. Anjali Deshpande",
        role: "Principal",
        message:
          "Our teachers know their students well. We celebrate effort as much as results, and we keep parents informed at every step of their child's journey.",
      },
      milestones: [
        { year: "1998", text: "School founded with Grades 6 to 8." },
        { year: "2006", text: "Science and computer laboratories opened." },
        { year: "2015", text: "Expanded to Grade 10 with a new academic block." },
        { year: "2026", text: "Launched the school ERP for students, staff and management." },
      ],
    },
    academics: {
      intro:
        "Our curriculum follows a national board framework, taught through discussion, practical work and regular formative assessment.",
      stages: [
        { name: "Middle school", grades: "Grades 6–8", focus: "Core literacy, numeracy and enquiry skills across all subjects." },
        { name: "Secondary school", grades: "Grades 9–10", focus: "Board examination preparation with subject depth and study skills." },
      ],
      subjects: ["English", "Hindi", "Mathematics", "Science", "Social Science", "Computer Science", "Physical Education"],
      assessment:
        "Students sit three unit tests and a half-yearly examination each year, alongside projects and practicals. Published results and attendance are available to students in the ERP.",
    },
    admissions: {
      intro: "We welcome applications for Grades 6 to 9. Places in each grade are limited and allocated through a transparent process.",
      steps: [
        { title: "Send an enquiry", text: "Use the contact form or visit the school office." },
        { title: "Campus visit", text: "Meet our admissions team and tour the school." },
        { title: "Interaction", text: "An informal age-appropriate interaction with the student." },
        { title: "Offer and enrolment", text: "Complete documents and fee formalities to confirm the seat." },
      ],
      documents: [
        "Birth certificate",
        "Previous school report card",
        "Transfer certificate (where applicable)",
        "Address proof",
        "Passport-size photographs",
      ],
      dates: [
        { label: "Enquiries open", value: "1 November" },
        { label: "Campus visits", value: "November – January" },
        { label: "Offers released", value: "February" },
        { label: "Session begins", value: "1 April" },
      ],
      feeNote:
        "The fee schedule is shared with families during the admissions process. Concessions are available for siblings and on merit.",
    },
    facilities: [
      { icon: "flask", title: "Science laboratories", text: "Separate physics, chemistry and biology labs with safety equipment." },
      { icon: "laptop", title: "Computer lab", text: "40 workstations for coding, research and digital skills." },
      { icon: "library", title: "Library", text: "Over 8,000 books, periodicals and a quiet reading room." },
      { icon: "trophy", title: "Sports ground", text: "Football, athletics track, basketball and indoor games." },
      { icon: "music", title: "Music and art rooms", text: "Dedicated studios for performing and visual arts." },
      { icon: "bus", title: "Transport", text: "GPS-tracked buses covering major routes in Demo City." },
      { icon: "stethoscope", title: "Health room", text: "A trained nurse on campus during school hours." },
      { icon: "shield", title: "Safe campus", text: "CCTV, visitor management and trained security staff." },
    ],
    faculty: [
      { name: "Dr. Anjali Deshpande", role: "Principal", department: "Leadership", qualification: "Ph.D. (Education)" },
      { name: "Kavita Kulkarni", role: "Senior Teacher", department: "Mathematics", qualification: "M.Sc., B.Ed." },
      { name: "Rahul Menon", role: "Teacher", department: "Science", qualification: "M.Sc., B.Ed." },
      { name: "Priya Iyer", role: "Teacher", department: "English", qualification: "M.A., B.Ed." },
      { name: "Meenakshi Joshi", role: "Teacher", department: "Hindi", qualification: "M.A., B.Ed." },
      { name: "Nandini Ghosh", role: "Teacher", department: "Social Science", qualification: "M.A., B.Ed." },
      { name: "Harpreet Kaur", role: "Teacher", department: "Computer Science", qualification: "M.C.A., B.Ed." },
      { name: "Suresh Yadav", role: "Sports Coordinator", department: "Physical Education", qualification: "M.P.Ed." },
    ],
    news: [
      {
        date: "2026-10-18",
        kind: "event",
        title: "Annual Sports Day in November",
        summary: "Track and field events for all grades. Families are welcome.",
      },
      {
        date: "2026-10-10",
        kind: "news",
        title: "Inter-house debate held",
        summary: "Students debated the role of technology in classrooms.",
      },
      {
        date: "2026-10-03",
        kind: "notice",
        title: "Half-yearly results published",
        summary: "Students can view their results in the ERP Portal.",
      },
      {
        date: "2026-09-05",
        kind: "news",
        title: "Teachers' Day celebrations",
        summary: "Students organised a special assembly for their teachers.",
      },
    ],
  },
};
