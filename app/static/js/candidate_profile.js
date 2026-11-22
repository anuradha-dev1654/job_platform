document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("profile-modal");
  const backdrop = document.getElementById("profile-modal-backdrop");
  const fields = document.getElementById("profile-modal-fields");
  const sectionName = document.getElementById("profile-section-name");
  const title = document.getElementById("profile-modal-title");
  const existing = window.profileSections || {};

  const configs = {
    basic: [
      ["name", "Full name", "text"], ["email", "Email address", "email"],
      ["headline", "Professional headline", "text"], ["location", "Location", "text"],
      ["phone", "Phone number", "tel"], ["gender", "Gender", "select:Male,Female,Non-binary,Prefer not to say"],
      ["birthday", "Date of birth", "date"]
    ],
    preferences: [
      ["job_types", "Preferred job type", "text"], ["availability", "Availability to work", "select:Immediate,15 days,30 days,60 days,Not available"],
      ["locations", "Preferred work location", "text"]
    ],
    education: [
      ["qualification", "Highest qualification", "text"], ["course", "Course", "text"],
      ["college", "College / University", "text"], ["graduation_year", "Graduation year", "number"],
      ["course_type", "Course type", "select:Full Time,Part Time,Distance,Online"]
    ],
    key_skills: [["skills", "Key skills (comma separated)", "text"]],
    languages: [["languages", "Languages (comma separated)", "text"]],
    internships: [["company", "Company", "text"], ["role", "Role", "text"], ["duration", "Duration", "text"], ["description", "Work and learning", "textarea"]],
    projects: [["title", "Project title", "text"], ["description", "Description", "textarea"], ["technologies", "Technologies", "text"], ["link", "Project link", "url"]],
    profile_summary: [["summary", "Professional summary", "textarea"]],
    certifications: [["name", "Certification name", "text"], ["issuer", "Issuing organisation", "text"], ["year", "Year", "text"], ["link", "Certificate link", "url"]],
    awards: [["title", "Award name", "text"], ["issuer", "Issuer", "text"], ["year", "Year", "text"], ["description", "Description", "textarea"]],
    clubs: [["organisation", "Organisation", "text"], ["position", "Position", "text"], ["duration", "Duration", "text"], ["responsibilities", "Responsibilities", "textarea"]],
    competitive_exams: [["exam", "Exam name", "text"], ["rank", "Rank", "text"], ["score", "Score", "text"], ["year", "Year", "text"]],
    employment: [["company", "Company", "text"], ["designation", "Designation", "text"], ["duration", "Duration", "text"], ["description", "Job responsibilities", "textarea"]],
    academic_achievements: [["title", "Achievement", "text"], ["institution", "Institution", "text"], ["year", "Year", "text"], ["description", "Description", "textarea"]]
  };

  const labels = {
    basic: "Edit personal details", preferences: "Career preferences", education: "Education",
    key_skills: "Key skills", languages: "Languages", internships: "Internships", projects: "Projects",
    profile_summary: "Profile summary", certifications: "Certifications", awards: "Awards",
    clubs: "Club & committees", competitive_exams: "Competitive exams", employment: "Employment",
    academic_achievements: "Academic achievements"
  };

  function valueFor(section, key) {
    if (section === "key_skills" && key === "skills") return (existing.key_skills && existing.key_skills.skills || []).join(", ");
    if (section === "languages" && key === "languages") return (existing.languages && existing.languages.languages || []).join(", ");
    return existing[section] ? (existing[section][key] || "") : "";
  }

  function basicValue(key) {
    if (window.profileBasic) return window.profileBasic[key] || "";
    const node = document.querySelector(".profile-header__content");
    if (!node) return "";
    if (key === "name") return node.querySelector("h1")?.textContent.trim() || "";
    if (key === "email") {
      const text = node.querySelector(".profile-facts")?.textContent || "";
      return text.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i)?.[0] || "";
    }
    if (key === "headline") return node.querySelector(".profile-headline")?.textContent.trim() || "";
    return "";
  }

  function openSection(section) {
    const config = configs[section];
    if (!config) return;
    sectionName.value = section;
    title.textContent = labels[section] || "Edit profile";
    fields.innerHTML = "";
    config.forEach(([key, label, type]) => {
      const wrap = document.createElement("label");
      wrap.className = "profile-field";
      wrap.text = "";
      wrap.append(document.createTextNode(label));
      let input;
      if (type.startsWith("select:")) {
        input = document.createElement("select");
        type.slice(7).split(",").forEach(optionText => {
          const option = document.createElement("option");
          option.textContent = optionText;
          option.value = optionText;
          input.append(option);
        });
      } else if (type === "textarea") {
        input = document.createElement("textarea");
        input.rows = 5;
      } else {
        input = document.createElement("input");
        input.type = type;
      }
      input.name = key;
      input.value = section === "basic" ? basicValue(key) : valueFor(section, key);
      if (key === "location" || key === "locations") {
        input.setAttribute("list", "profile-location-options");
        input.setAttribute("placeholder", "Enter any city or location");
      }
      wrap.append(input);
      fields.append(wrap);
    });
    if (!document.getElementById("profile-location-options")) {
      const datalist = document.createElement("datalist");
      datalist.id = "profile-location-options";
      fields.append(datalist);
    }
    const datalist = document.getElementById("profile-location-options");
    const locationField = fields.querySelector('[name="location"], [name="locations"]');
    if (locationField && datalist) {
      const loadLocations = async () => {
        try {
          const response = await fetch(`/api/locations?q=${encodeURIComponent(locationField.value || "")}`);
          if (!response.ok) return;
          const data = await response.json();
          datalist.innerHTML = "";
          (data.locations || []).forEach(location => {
            const option = document.createElement("option");
            option.value = location;
            datalist.append(option);
          });
        } catch (_) {}
      };
      loadLocations();
      locationField.addEventListener("input", loadLocations);
    }
    modal.showModal();
    backdrop.hidden = false;
  }

  function closeModal() {
    if (modal.open) modal.close();
    backdrop.hidden = true;
  }

  document.querySelectorAll("[data-section]").forEach(button => {
    button.addEventListener("click", () => openSection(button.dataset.section));
  });
  document.getElementById("profile-modal-close")?.addEventListener("click", closeModal);
  document.getElementById("profile-modal-cancel")?.addEventListener("click", closeModal);
  backdrop?.addEventListener("click", closeModal);
});
