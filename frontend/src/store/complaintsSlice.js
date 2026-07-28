import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { extractFromText, extractFromFile, saveComplaint, fetchComplaints } from "../api/client";

const emptyForm = {
  product_name: "",
  batch_number: "",
  complainant_name: "",
  complainant_email: "",
  date_of_incident: "",
  complaint_description: "",
};

export const runExtraction = createAsyncThunk(
  "complaints/runExtraction",
  async ({ rawText, file, sourceChannel }, { rejectWithValue }) => {
    try {
      const data = file ? await extractFromFile(file) : await extractFromText(rawText);
      return { ...data, sourceChannel, rawText };
    } catch (err) {
      return rejectWithValue(err?.response?.data?.detail || "Extraction failed. Check the backend is running and GROQ_API_KEY is set.");
    }
  }
);

export const persistComplaint = createAsyncThunk(
  "complaints/persistComplaint",
  async (_, { getState, rejectWithValue }) => {
    try {
      const { form, assessment, sourceChannel, rawText } = getState().complaints;
      const payload = {
        ...form,
        source_channel: sourceChannel,
        raw_input_text: rawText,
        assessment,
      };
      return await saveComplaint(payload);
    } catch (err) {
      return rejectWithValue(err?.response?.data?.detail || "Could not save complaint.");
    }
  }
);

export const loadComplaints = createAsyncThunk("complaints/loadComplaints", async () => {
  return await fetchComplaints();
});

const complaintsSlice = createSlice({
  name: "complaints",
  initialState: {
    form: emptyForm,
    assessment: null,
    sourceChannel: "Manual Entry",
    rawText: "",

    list: [],
    listStatus: "idle",

    extractStatus: "idle",
    extractError: null,

    saveStatus: "idle",
    saveError: null,
  },
  reducers: {
    updateFormField(state, action) {
      const { field, value } = action.payload;
      state.form[field] = value;
    },
    resetIntake(state) {
      state.form = emptyForm;
      state.assessment = null;
      state.rawText = "";
      state.extractStatus = "idle";
      state.saveStatus = "idle";
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(runExtraction.pending, (state) => {
        state.extractStatus = "loading";
        state.extractError = null;
        state.saveStatus = "idle";
      })
      .addCase(runExtraction.fulfilled, (state, action) => {
        state.extractStatus = "succeeded";
        state.form = action.payload.extracted;
        state.assessment = action.payload.assessment;
        state.sourceChannel = action.payload.sourceChannel;
        state.rawText = action.payload.rawText || "";
      })
      .addCase(runExtraction.rejected, (state, action) => {
        state.extractStatus = "failed";
        state.extractError = action.payload || action.error.message;
      })
      .addCase(persistComplaint.pending, (state) => {
        state.saveStatus = "loading";
        state.saveError = null;
      })
      .addCase(persistComplaint.fulfilled, (state, action) => {
        state.saveStatus = "succeeded";
        state.list.unshift(action.payload);
      })
      .addCase(persistComplaint.rejected, (state, action) => {
        state.saveStatus = "failed";
        state.saveError = action.payload || action.error.message;
      })
      .addCase(loadComplaints.pending, (state) => {
        state.listStatus = "loading";
      })
      .addCase(loadComplaints.fulfilled, (state, action) => {
        state.listStatus = "succeeded";
        state.list = action.payload;
      })
      .addCase(loadComplaints.rejected, (state) => {
        state.listStatus = "failed";
      });
  },
});

export const { updateFormField, resetIntake } = complaintsSlice.actions;
export default complaintsSlice.reducer;
