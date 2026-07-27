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
import { askStaffingChat, getAnalytics, getRecommendations, getUtilization } from "../services/api";

const AXIS_TICK = { fontSize: 12, fill: "#4c6370" };
const STAFFING_QUERY_HINT =
  "Ask about staffing, skills, experience, availability, utilization, bench, assignments, or project allocation decisions.";
const STAFFING_KEYWORDS = [
  "employee",
  "employees",
  "resource",
  "resources",
  "staff",
  "staffing",
  "allocation",
  "allocate",
  "unassign",
  "assign",
  "project",
  "projects",
  "skill",
  "skills",
  "availability",
  "utilization",
  "bench",
  "candidate",
  "candidates",
  "role",
  "roles",
  "experience",
];

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

const validateStaffingPrompt = (value) => {
  const normalized = value.trim().toLowerCase();

  if (!normalized) {
    return "Enter a staffing question before sending the request.";
  }

  if (normalized.length < 12) {
    return "Enter a more specific staffing question so the AI can respond meaningfully.";
  }

  if (!STAFFING_KEYWORDS.some((keyword) => normalized.includes(keyword))) {
    return STAFFING_QUERY_HINT;
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
  const [chatPrompt, setChatPrompt] = useState("");
  const [chatResponse, setChatResponse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [recommendLoading, setRecommendLoading] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState("");
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

  const runRecommendation = async () => {
    if (!canManage) {
      setError("Recommendation generation is available only for admin and manager roles.");
      return;
    }
    const payload = {
      project_name: "Healthcare Modernization",
      required_skills: skills.split(",").map((s) => s.trim()).filter(Boolean),
      preferred_certifications: ["Azure-AZ900"],
      min_experience: 4,
      required_count: 3,
      location: "Remote",
      domain: "Healthcare",
    };
    setRecommendLoading(true);
    setError("");
    try {
      const data = await getRecommendations(payload);
      setRecommendations(data.recommendations || []);
    } catch (err) {
      const message = err?.response?.data?.detail || err?.message || "Failed to generate recommendation.";
      setError(message);
    } finally {
      setRecommendLoading(false);
    }
  };

  const handleAskStaffingChat = async () => {
    const validationError = validateStaffingPrompt(chatPrompt);
    if (validationError) {
      setChatError(validationError);
      setChatResponse(null);
      return;
    }

    setChatLoading(true);
    setChatError("");
    try {
      const response = await askStaffingChat({
        query: chatPrompt.trim(),
        top_k: 5,
      });
      setChatResponse(response);
    } catch (err) {
      const message = err?.response?.data?.detail || err?.message || "Failed to fetch AI chat response.";
      setChatError(message);
      setChatResponse(null);
    } finally {
      setChatLoading(false);
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
                <Box sx={{ display: "flex", gap: 2, mb: 3, flexWrap: "wrap" }}>
                  <TextField
                    fullWidth
                    label="Required Skills (comma separated)"
                    value={skills}
                    onChange={(e) => setSkills(e.target.value)}
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
                {recommendations.map((r) => (
                  <Box key={r.employee_id} sx={{ p: 2, border: "1px solid #e5ddd2", borderRadius: 2, mb: 1.5 }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                      {r.employee_name} ({r.employee_id}) - {r.match_score}
                    </Typography>
                    <Typography variant="body2" sx={{ mb: 1 }}>{r.recommendation_reason}</Typography>
                    <Chip label={`Availability: ${r.availability}`} sx={{ mr: 1, mb: 1 }} />
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

            <Card sx={{ ...sectionCardStyle, borderRadius: 3, mb: 5 }}>
              <CardContent sx={{ p: 2.5 }}>
                <SectionHeader
                  title="AI Recommendation Chat"
                  subtitle="Ask staffing questions about skills, bench, utilization, and project allocation decisions."
                />
                <Alert severity="info" sx={{ mb: 2 }}>
                  {STAFFING_QUERY_HINT}
                </Alert>
                {chatError && <Alert severity="error" sx={{ mb: 2 }}>{chatError}</Alert>}
                <Box sx={{ display: "flex", gap: 2, mb: 3, flexWrap: "wrap" }}>
                  <TextField
                    fullWidth
                    multiline
                    minRows={3}
                    label="Ask the staffing assistant"
                    placeholder="Example: Which employees with Azure skills and lower utilization should we prioritize for the next healthcare project?"
                    value={chatPrompt}
                    onChange={(e) => {
                      setChatPrompt(e.target.value);
                      if (chatError) {
                        setChatError("");
                      }
                    }}
                  />
                  <Button
                    variant="contained"
                    onClick={handleAskStaffingChat}
                    sx={{ background: "#9f4f35", minWidth: 150 }}
                    disabled={chatLoading}
                  >
                    {chatLoading ? "Thinking..." : "Ask AI"}
                  </Button>
                </Box>
                {!chatResponse?.answer && (
                  <Typography variant="body2" sx={{ color: "#65737d" }}>
                    The response is limited to workforce staffing and allocation use cases.
                  </Typography>
                )}
                {chatResponse?.answer && (
                  <Box sx={{ p: 2, border: "1px solid #e5ddd2", borderRadius: 2, background: "#fffaf5" }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1 }}>
                      AI Response
                    </Typography>
                    <Typography variant="body2" sx={{ whiteSpace: "pre-wrap", mb: chatResponse?.sources?.length ? 1.5 : 0 }}>
                      {chatResponse.answer}
                    </Typography>
                    {chatResponse?.sources?.length > 0 && (
                      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
                        {chatResponse.sources.map((sourceId) => (
                          <Chip key={sourceId} label={`Source: ${sourceId}`} size="small" variant="outlined" />
                        ))}
                      </Stack>
                    )}
                  </Box>
                )}
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
