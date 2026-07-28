import axios from "axios";

export const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

export async function extractFromText(rawText) {
  const { data } = await api.post("/complaints/extract", { raw_text: rawText });
  return data;
}

export async function extractFromFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/complaints/extract-file", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function saveComplaint(payload) {
  const { data } = await api.post("/complaints", payload);
  return data;
}

export async function fetchComplaints() {
  const { data } = await api.get("/complaints");
  return data;
}
