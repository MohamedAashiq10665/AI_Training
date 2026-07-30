import React, { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  CircularProgress,
  Card,
  CardContent,
  Container,
  Grid,
  Typography,
  Button,
  TextField,
  Chip,
  Stack,
  Divider,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
} from "@mui/material";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
} from "recharts";
import { getAnalytics, getRecommendations, getUtilization } from "../services/api";

const AXIS_TICK = { fontSize: 12, fill: "#4c6370" };
const SKILL_FORMAT_HINT = "Enter comma-separated skills only, such as Python, Azure, React, Data Engineering, or Power BI.";
const INTENT_FORMAT_HINT =
  "Use a staffing sentence, for example: Suggest 2 Azure engineers with minimum 3 years experience.";
const INVALID_SKILL_TERMS = new Set([
  "hi",
  "hello",
  "hey",
  "happy",
  "birthday",
  "thanks",
  "thank",
  "who",
  "what",
  "when",
  "where",
  "why",
  "how",
  "please",
  "find",
  "show",
  "give",
  "tell",
  "recommend",
  "suggest",
  "need",
  "want",
  "employee",
  "employees",
  "project",
  "projects",
  "allocation",
  "utilization",
  "bench",
  "staffing",
]);

const truncateLabel = (value, max = 12) => {
  if (!value) return "";
  return value.length > max ? `${value.slice(0, max - 1)}...` : value;
};

const formatMonth = (value) => {
  if (!value || value.length < 7) return value;
  const year = value.slice(2, 4);
  const month = value.slice(5, 7);
  return `${month}/${year}`;
};

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <Box
      sx={{
        px: 1.5,
        py: 1,
        borderRadius: 1.5,
        border: "1px solid #d9d3ca",
        background: "#fffdf9",
        boxShadow: 2,
      }}
    >
      <Typography variant="caption" sx={{ color: "#6d7d87", display: "block", mb: 0.5 }}>
        {label}
      </Typography>
      <Typography variant="body2" sx={{ fontWeight: 700, color: "#21303a" }}>
        {payload[0].value}
      </Typography>
    </Box>
  );
}

const sectionCardStyle = {
  borderRadius: 3,
  border: "1px solid #e9e2d7",
  background: "#fffdfa",
  boxShadow: "0 4px 16px rgba(20, 35, 45, 0.06)",
};

const chartCardStyle = {
  ...sectionCardStyle,
  width: { xs: "100%", lg: 500 },
  minWidth: { lg: 500 },
  maxWidth: { lg: 500 },
  height: { xs: 380, sm: 400, md: 420, lg: 440 },
  mx: { xs: 0, lg: "auto" },
};

const metricCard = (title, value) => (
  <Card sx={{ ...sectionCardStyle, minHeight: 128 }}>
    <CardContent sx={{ p: 2.5 }}>
      <Typography variant="overline" color="text.secondary">
        {title}
      </Typography>
      <Typography variant="h4" sx={{ fontWeight: 700, color: "#23303b", mt: 0.5 }}>
        {value}
      </Typography>
    </CardContent>
  </Card>
);

const parseSkills = (value) => value.split(",").map((skill) => skill.trim()).filter(Boolean);

const componentChipColor = (score) => {
  if (score >= 0.75) return "success";
  if (score >= 0.5) return "warning";
  return "error";
};

const componentPercent = (score) => `${Math.round((Number(score) || 0) * 100)}%`;

const looksLikeNaturalLanguageIntent = (value) => {
  const normalized = String(value || "").trim().toLowerCase();
  if (!normalized || normalized.includes(",")) return false;
  const wordCount = normalized.split(/\s+/).filter(Boolean).length;
  if (wordCount < 4) return false;
  return /(assign|allocate|need|require|staff|recommend|find|experience|years?|resources?|engineers?)/.test(normalized);
};

const extractDomainFromIntent = (value) => {
  const normalized = String(value || "").trim().toLowerCase();
  if (!normalized) return null;
  const domainAliases = {
    healthcare: "Healthcare",
    finance: "Finance",
    retail: "Retail",
    "public sector": "Public Sector",
    telecom: "Telecom",
  };
  for (const [token, canonical] of Object.entries(domainAliases)) {
    const pattern = new RegExp(`(?<!\\w)${token.replace(" ", "\\s+")}(?!\\w)`, "i");
    if (pattern.test(normalized)) {
      return canonical;
    }
  }
  return null;
};

const extractRequestedCountFromIntent = (value) => {
  const normalized = String(value || "").trim().toLowerCase();
  if (!normalized) return null;

  let match = normalized.match(/\b(assign|allocate|need|require|staff|find|recommend|suggest)\s+(\d{1,2})\b/);
  if (!match) {
    match = normalized.match(/\b(\d{1,2})\s+(engineers?|developers?|resources?|people|staff|candidates?)\b/);
  }
  if (!match) {
    match = normalized.match(/\b(\d{1,2})\s+(?:[a-z0-9.+#&/_-]+\s+){0,4}(engineers?|developers?|resources?|people|staff|candidates?)\b/);
  }
  if (!match) return null;

  const parsed = Number(match[2] || match[1]);
  if (!Number.isFinite(parsed)) return null;
  return Math.max(1, parsed);
};

const validateRequiredSkills = (value, inputMode) => {
  const normalized = String(value || "").trim();
  if (!normalized) {
    return "Enter at least one required skill or staffing sentence before requesting recommendations.";
  }

  if (normalized.length > 200) {
    return "Keep the recommendation input under 200 characters.";
  }

  if (inputMode === "intent") {
    if (!looksLikeNaturalLanguageIntent(normalized)) {
      return INTENT_FORMAT_HINT;
    }
    return "";
  }

  const parsedSkills = parseSkills(value);

  if (parsedSkills.length === 0) {
    return "Enter at least one required skill before requesting staffing recommendations.";
  }

  if (parsedSkills.some((skill) => skill.length < 2)) {
    return "Each required skill must contain at least 2 characters.";
  }

  for (const skill of parsedSkills) {
    const skillTerms = skill.toLowerCase().replaceAll("/", " ").replaceAll("-", " ").split(/\s+/).filter(Boolean);
    if (skillTerms.length > 4) {
      return SKILL_FORMAT_HINT;
    }
    if (skillTerms.some((term) => INVALID_SKILL_TERMS.has(term))) {
      return SKILL_FORMAT_HINT;
    }
    if (!/^[A-Za-z0-9][A-Za-z0-9 .#+&/_-]{0,39}$/.test(skill)) {
      return SKILL_FORMAT_HINT;
    }
  }

  return "";
};

function SectionHeader({ title, subtitle, action }) {
  return (
    <Stack
      direction={{ xs: "column", md: "row" }}
      justifyContent="space-between"
      alignItems={{ xs: "start", md: "center" }}
      spacing={1}
      sx={{ mb: 2 }}
    >
      <Box>
        <Typography variant="h5" sx={{ fontWeight: 750, color: "#1f2d38" }}>
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="body2" sx={{ color: "#60727d", mt: 0.4 }}>
            {subtitle}
          </Typography>
        )}
      </Box>
      {action}
    </Stack>
  );
}

export default function Dashboard({ role, onLogout, onShowEmployees }) {
  const [analytics, setAnalytics] = useState(null);
  const [utilization, setUtilization] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [skills, setSkills] = useState("Python,Azure");
  const [recommendationInputMode, setRecommendationInputMode] = useState("skills");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [recommendLoading, setRecommendLoading] = useState(false);
  const [recommendationError, setRecommendationError] = useState("");
  const [recommendationNotice, setRecommendationNotice] = useState("");
  const [requestedCount, setRequestedCount] = useState(0);
  const [returnedCount, setReturnedCount] = useState(0);
  const [activeDomainCriterion, setActiveDomainCriterion] = useState("");
  const isViewer = role === "viewer";
  const canManage = role === "admin" || role === "manager";

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        setAnalytics(await getAnalytics());
        setUtilization(await getUtilization());
      } catch (err) {
        const message = err?.response?.data?.detail || err?.message || "Failed to load dashboard data.";
        setError(message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const benchData = useMemo(() => {
    if (!analytics?.bench_by_skill) return [];
    return Object.entries(analytics.bench_by_skill)
      .map(([skill, count]) => ({ skill, count }))
      .slice(0, 6);
  }, [analytics]);

  const trendData = useMemo(() => {
    if (!utilization?.historical_allocation_trend) return [];
    return Object.entries(utilization.historical_allocation_trend).map(([month, count]) => ({ month, count }));
  }, [utilization]);

  const skillDemandData = useMemo(() => {
    if (!analytics?.skill_demand_trend) return [];
    return Object.entries(analytics.skill_demand_trend)
      .map(([skill, count]) => ({ skill, count }))
      .slice(0, 6);
  }, [analytics]);

  const projectDemandData = useMemo(() => {
    if (!analytics?.upcoming_project_demand) return [];
    return Object.entries(analytics.upcoming_project_demand)
      .map(([domain, count]) => ({ domain, count }))
      .slice(0, 6);
  }, [analytics]);

  const recommendationSummary = useMemo(() => {
    const total = recommendations.length;
    if (!total) {
      return {
        total: 0,
        skillMatched: 0,
        experienceQualified: 0,
        certificationMatched: 0,
        availabilityQualified: 0,
        domainMatched: 0,
        fullyQualified: 0,
      };
    }

    const skillMatched = recommendations.filter((item) => (item?.missing_skills || []).length === 0).length;
    const experienceQualified = recommendations.filter((item) => Number(item?.component_scores?.experience || 0) >= 1).length;
    const certificationMatched = recommendations.filter((item) => Number(item?.component_scores?.certifications || 0) > 0).length;
    const availabilityQualified = recommendations.filter((item) => Number(item?.component_scores?.availability || 0) >= 1).length;
    const domainMatched = activeDomainCriterion
      ? recommendations.filter(
          (item) =>
            String(item?.latest_project_domain || "").trim().toLowerCase() ===
            String(activeDomainCriterion || "").trim().toLowerCase()
        ).length
      : 0;
    const fullyQualified = recommendations.filter((item) => {
      const noMissingSkills = (item?.missing_skills || []).length === 0;
      const experienceOk = Number(item?.component_scores?.experience || 0) >= 1;
      const certOk = Number(item?.component_scores?.certifications || 0) > 0;
      const availabilityOk = Number(item?.component_scores?.availability || 0) >= 1;
      return noMissingSkills && experienceOk && certOk && availabilityOk;
    }).length;

    return {
      total,
      skillMatched,
      experienceQualified,
      certificationMatched,
      availabilityQualified,
      domainMatched,
      fullyQualified,
    };
  }, [recommendations, activeDomainCriterion]);

  const runRecommendation = async () => {
    if (!canManage) {
      setError("Recommendation generation is available only for admin and manager roles.");
      return;
    }

    const normalizedInput = String(skills || "").trim();
    const effectiveInputMode =
      recommendationInputMode === "intent" || looksLikeNaturalLanguageIntent(normalizedInput)
        ? "intent"
        : "skills";

    const validationError = validateRequiredSkills(normalizedInput, effectiveInputMode);
    if (validationError) {
      setRecommendationError(validationError);
      setRecommendations([]);
      setRecommendationNotice("");
      setRequestedCount(0);
      setReturnedCount(0);
      setActiveDomainCriterion("");
      return;
    }

    const payload = {
      project_name: "Healthcare Modernization",
      required_skills: effectiveInputMode === "intent" ? [normalizedInput] : parseSkills(normalizedInput),
      preferred_certifications: ["Azure-AZ900"],
      min_experience: effectiveInputMode === "intent" ? 0 : 4,
      required_count: 10,
      location: effectiveInputMode === "intent" ? null : "Remote",
      domain: effectiveInputMode === "intent" ? null : "Healthcare",
    };
    const expectedRequestedCount =
      effectiveInputMode === "intent"
        ? extractRequestedCountFromIntent(normalizedInput) ?? payload.required_count
        : payload.required_count;
    const effectiveDomainCriterion = effectiveInputMode === "intent"
      ? extractDomainFromIntent(normalizedInput)
      : payload.domain;

    setRecommendLoading(true);
    setError("");
    setRecommendationError("");
    setRecommendationNotice("");
    setRequestedCount(expectedRequestedCount);
    setReturnedCount(0);
    setActiveDomainCriterion(effectiveDomainCriterion || "");
    try {
      const data = await getRecommendations(payload);
      const receivedRecommendations = data?.recommendations || [];
      const intentRequestedCount = effectiveInputMode === "intent" ? extractRequestedCountFromIntent(normalizedInput) : null;
      const effectiveRequestedCount = Number(data?.requested_count ?? intentRequestedCount ?? payload.required_count ?? 0) || 0;
      const effectiveReturnedCount = Number(data?.returned_count ?? receivedRecommendations.length ?? 0) || 0;
      const fallbackNotice =
        effectiveRequestedCount > 0 && effectiveReturnedCount < effectiveRequestedCount
          ? `Only ${effectiveReturnedCount} recommendation(s) were retrieved. We could not find enough candidates to satisfy the requested ${effectiveRequestedCount}.`
          : "";

      setRecommendations(receivedRecommendations);
  setRequestedCount(effectiveRequestedCount > 0 ? effectiveRequestedCount : expectedRequestedCount);
      setReturnedCount(effectiveReturnedCount);
      setRecommendationNotice(data?.retrieval_notice || fallbackNotice);
    } catch (err) {
      const message = err?.response?.data?.detail || err?.message || "Failed to generate recommendation.";
      setError(message);
    } finally {
      setRecommendLoading(false);
    }
  };

  return (
    <Box sx={{ minHeight: "100vh", background: "linear-gradient(180deg, #f5f2eb 0%, #fefdfb 100%)", py: 5 }}>
      <Container maxWidth={false} sx={{ px: { xs: 2, sm: 3, md: 4, lg: 6, xl: 8 }, maxWidth: 1840, mx: "auto" }}>
        <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" alignItems={{ xs: "start", md: "center" }} spacing={2} sx={{ mb: 4 }}>
          <Box>
            <Typography variant="h3" sx={{ fontWeight: 800, color: "#1e2a33", mb: 1 }}>
              AI Resource Allocation Command Center
            </Typography>
            <Typography variant="body1" sx={{ color: "#415564" }}>
              RAG-powered staffing recommendations, bench insights, and utilization analytics.
            </Typography>
            <Box sx={{ mt: 1 }}>
              <Chip
                size="small"
                label={isViewer ? "Role: Viewer (Read Only)" : `Role: ${role || "viewer"}`}
                color={isViewer ? "warning" : "success"}
                variant="outlined"
              />
            </Box>
          </Box>
          <Stack direction="row" spacing={1.5}>
            <Button variant="outlined" onClick={onShowEmployees} sx={{ borderRadius: 2 }}>
              Employees
            </Button>
            <Button variant="outlined" color="inherit" onClick={onLogout} sx={{ borderRadius: 2 }}>
              Logout
            </Button>
          </Stack>
        </Stack>

        {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}

        {loading ? (
          <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            <Card sx={{ ...sectionCardStyle, borderRadius: 3, mb: 5 }}>
              <CardContent sx={{ p: 2.5 }}>
                <SectionHeader
                  title="AI Staffing Recommendation"
                  subtitle={canManage ? "Generate role-fit suggestions with explainable match details." : "Available for manager/admin roles. Viewer has read-only access."}
                />
                {!canManage && (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    Recommendation generation is disabled for viewer role.
                  </Alert>
                )}
                {recommendationError && <Alert severity="error" sx={{ mb: 2 }}>{recommendationError}</Alert>}
                {recommendationNotice && <Alert severity="info" sx={{ mb: 2 }}>{recommendationNotice}</Alert>}
                <Box sx={{ display: "flex", gap: 2, mb: 3, flexWrap: "wrap" }}>
                  <FormControl sx={{ minWidth: { xs: "100%", sm: 250 } }} disabled={!canManage}>
                    <InputLabel id="recommendation-input-mode-label">Recommendation Mode</InputLabel>
                    <Select
                      labelId="recommendation-input-mode-label"
                      value={recommendationInputMode}
                      label="Recommendation Mode"
                      onChange={(e) => {
                        const nextMode = e.target.value;
                        setRecommendationInputMode(nextMode);
                        setSkills(nextMode === "intent" ? "Suggest 2 Azure engineers with minimum 3 years experience" : "Python,Azure");
                        setRecommendationError("");
                      }}
                    >
                      <MenuItem value="skills">Skill List Mode</MenuItem>
                      <MenuItem value="intent">Natural Language Mode</MenuItem>
                    </Select>
                  </FormControl>
                  <TextField
                    fullWidth
                    label={recommendationInputMode === "intent" ? "Staffing Request" : "Required Skills (comma separated)"}
                    value={skills}
                    onChange={(e) => {
                      setSkills(e.target.value);
                      if (recommendationError) {
                        setRecommendationError("");
                      }
                    }}
                    helperText={recommendationInputMode === "intent" ? INTENT_FORMAT_HINT : SKILL_FORMAT_HINT}
                    disabled={!canManage}
                  />
                  <Button variant="contained" onClick={runRecommendation} sx={{ background: "#1f6b75", minWidth: 150 }} disabled={recommendLoading || !canManage}>
                    {recommendLoading ? "Recommending..." : "Recommend"}
                  </Button>
                </Box>
                {recommendations.length === 0 && (
                  <Typography variant="body2" sx={{ color: "#65737d", mb: 2 }}>
                    No recommendations yet. Enter skills and click Recommend.
                  </Typography>
                )}
                {recommendations.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="subtitle2" sx={{ color: "#40535f", mb: 1, fontWeight: 700 }}>
                      Recommendation Coverage Summary
                    </Typography>
                    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                      <Chip size="small" label={`Requested: ${requestedCount > 0 ? requestedCount : "-"}`} />
                      <Chip size="small" label={`Returned: ${returnedCount > 0 ? returnedCount : recommendationSummary.total}`} />
                      <Chip size="small" color="success" label={`Skill Match: ${recommendationSummary.skillMatched}`} />
                      <Chip size="small" color="success" label={`Experience Qualified: ${recommendationSummary.experienceQualified}`} />
                      <Chip size="small" color="success" label={`Certification Match: ${recommendationSummary.certificationMatched}`} />
                      <Chip size="small" color="success" label={`Availability Qualified: ${recommendationSummary.availabilityQualified}`} />
                      <Chip
                        size="small"
                        color={activeDomainCriterion ? "success" : "default"}
                        label={
                          activeDomainCriterion
                            ? `Domain Match (${activeDomainCriterion}): ${recommendationSummary.domainMatched}`
                            : "Domain Match: N/A"
                        }
                      />
                      <Chip size="small" color="primary" label={`Fully Qualified: ${recommendationSummary.fullyQualified}`} />
                    </Stack>
                  </Box>
                )}
                {recommendations.map((r) => (
                  <Box key={r.employee_id} sx={{ p: 2, border: "1px solid #e5ddd2", borderRadius: 2, mb: 1.5 }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                      {r.employee_name} ({r.employee_id}) - {r.match_score}
                    </Typography>
                    <Typography variant="body2" sx={{ color: "#5f6f7a", mb: 0.7 }}>
                      Role: {r.role || "-"} | Primary Skill: {r.primary_skill || "-"} | Secondary Skill: {r.secondary_skill || "-"}
                    </Typography>
                    <Typography variant="body2" sx={{ color: "#5f6f7a", mb: 0.7 }}>
                      Experience: {Number.isFinite(Number(r.years_experience)) ? `${r.years_experience} years` : "-"} | Certifications: {r.certifications || "-"}
                    </Typography>
                    <Typography variant="body2" sx={{ color: "#5f6f7a", mb: 1 }}>
                      Latest Project: {r.latest_project_name || "-"} | Domain: {r.latest_project_domain || "-"}
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 1 }}>{r.recommendation_reason}</Typography>
                    <Chip label={`Availability: ${r.availability}`} sx={{ mr: 1, mb: 1 }} />
                    <Chip
                      color={componentChipColor(r?.component_scores?.experience)}
                      label={`Experience Fit: ${componentPercent(r?.component_scores?.experience)}`}
                      sx={{ mr: 1, mb: 1 }}
                    />
                    <Chip
                      color={componentChipColor(r?.component_scores?.certifications)}
                      label={`Certification Fit: ${componentPercent(r?.component_scores?.certifications)}`}
                      sx={{ mr: 1, mb: 1 }}
                    />
                    <Chip
                      color={componentChipColor(r?.component_scores?.availability)}
                      label={`Availability Fit: ${componentPercent(r?.component_scores?.availability)}`}
                      sx={{ mr: 1, mb: 1 }}
                    />
                    {r.skills_matched?.map((s) => (
                      <Chip key={`${r.employee_id}-${s}`} color="success" label={`Matched: ${s}`} sx={{ mr: 1, mb: 1 }} />
                    ))}
                    {r.missing_skills?.map((s) => (
                      <Chip key={`${r.employee_id}-missing-${s}`} color="warning" label={`Missing: ${s}`} sx={{ mr: 1, mb: 1 }} />
                    ))}
                  </Box>
                ))}
              </CardContent>
            </Card>

            <Box sx={{ mb: 5 }}>
              <SectionHeader title="Workforce Snapshot" subtitle="Current bench health and utilization coverage." />
              <Grid container spacing={3} columns={12}>
                <Grid item xs={12} sm={6} md={6} lg={3}>{metricCard("Total Employees", analytics?.total_employees ?? "-")}</Grid>
                <Grid item xs={12} sm={6} md={6} lg={3}>{metricCard("Available Employees", analytics?.available_employees ?? "-")}</Grid>
                <Grid item xs={12} sm={6} md={6} lg={3}>{metricCard("Bench %", analytics ? `${analytics.bench_percentage}%` : "-")}</Grid>
                <Grid item xs={12} sm={6} md={6} lg={3}>{metricCard("Utilization", analytics ? `${analytics.resource_utilization}%` : "-")}</Grid>
              </Grid>
            </Box>

            <Box sx={{ mb: 5 }}>
              <SectionHeader title="Workforce Analytics" subtitle="Bench composition and allocation behavior over time." />
              <Grid container spacing={3.5} columns={12}>
                <Grid item xs={12} md={12} lg={6}>
                  <Card sx={chartCardStyle}>
                    <CardContent sx={{ p: 2.5 }}>
                      <Typography variant="h6" sx={{ mb: 1 }}>Bench by Skill</Typography>
                      <Divider sx={{ mb: 2 }} />
                      <Box sx={{ height: { xs: 280, sm: 300, md: 310, lg: 320 } }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart
                            data={benchData}
                            layout="vertical"
                            margin={{ top: 8, right: 18, left: 12, bottom: 8 }}
                          >
                            <XAxis type="number" tick={AXIS_TICK} />
                            <YAxis
                              type="category"
                              dataKey="skill"
                              width={130}
                              tick={AXIS_TICK}
                              tickFormatter={(value) => truncateLabel(value, 12)}
                            />
                            <Tooltip content={<ChartTooltip />} />
                            <Bar dataKey="count" fill="#cd6a3d" radius={[6, 6, 6, 6]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={12} lg={6}>
                  <Card sx={chartCardStyle}>
                    <CardContent sx={{ p: 2.5 }}>
                      <Typography variant="h6" sx={{ mb: 1 }}>Historical Allocation Trend</Typography>
                      <Divider sx={{ mb: 2 }} />
                      <Box sx={{ height: { xs: 280, sm: 300, md: 310, lg: 320 } }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={trendData.slice(-12)} margin={{ top: 8, right: 20, left: 4, bottom: 10 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#dfd8cc" />
                            <XAxis
                              dataKey="month"
                              tick={AXIS_TICK}
                              tickFormatter={formatMonth}
                              minTickGap={24}
                            />
                            <YAxis tick={AXIS_TICK} />
                            <Tooltip content={<ChartTooltip />} />
                            <Line
                              type="monotone"
                              dataKey="count"
                              stroke="#1f6b75"
                              strokeWidth={2.5}
                              dot={{ r: 2.8 }}
                              activeDot={{ r: 4 }}
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Box>

            <Box sx={{ mb: 5 }}>
              <SectionHeader title="Demand Signals" subtitle="Top skills and domains driving staffing demand." />
              <Grid container spacing={3.5} columns={12}>
                <Grid item xs={12} md={12} lg={6}>
                  <Card sx={chartCardStyle}>
                    <CardContent sx={{ p: 2.5 }}>
                      <Typography variant="h6" sx={{ mb: 1 }}>Skill Demand Trend</Typography>
                      <Divider sx={{ mb: 2 }} />
                      <Box sx={{ height: { xs: 280, sm: 300, md: 310, lg: 320 } }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart
                            data={skillDemandData}
                            layout="vertical"
                            margin={{ top: 8, right: 18, left: 12, bottom: 8 }}
                          >
                            <XAxis type="number" tick={AXIS_TICK} />
                            <YAxis
                              type="category"
                              dataKey="skill"
                              width={130}
                              tick={AXIS_TICK}
                              tickFormatter={(value) => truncateLabel(value, 12)}
                            />
                            <Tooltip content={<ChartTooltip />} />
                            <Bar dataKey="count" fill="#1f6b75" radius={[6, 6, 6, 6]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={12} md={12} lg={6}>
                  <Card sx={chartCardStyle}>
                    <CardContent sx={{ p: 2.5 }}>
                      <Typography variant="h6" sx={{ mb: 1 }}>Upcoming Project Demand</Typography>
                      <Divider sx={{ mb: 2 }} />
                      <Box sx={{ height: { xs: 280, sm: 300, md: 310, lg: 320 } }}>
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart
                            data={projectDemandData}
                            layout="vertical"
                            margin={{ top: 8, right: 18, left: 12, bottom: 8 }}
                          >
                            <XAxis type="number" tick={AXIS_TICK} />
                            <YAxis
                              type="category"
                              dataKey="domain"
                              width={130}
                              tick={AXIS_TICK}
                              tickFormatter={(value) => truncateLabel(value, 14)}
                            />
                            <Tooltip content={<ChartTooltip />} />
                            <Bar dataKey="count" fill="#9f4f35" radius={[6, 6, 6, 6]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Box>

          </>
        )}
      </Container>
    </Box>
  );
}
