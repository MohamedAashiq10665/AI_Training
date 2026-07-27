import React, { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  Card,
  CardContent,
  CircularProgress,
  Container,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TablePagination,
  TableHead,
  TableRow,
  TableSortLabel,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import {
  assignEmployeeToProject,
  getEmployees,
  getProjectAiRecommendations,
  getProjectDetails,
  getProjects,
  unassignEmployeeFromProject,
} from "../services/api";

const pageCardStyle = {
  borderRadius: 3,
  border: "1px solid #e9e2d7",
  background: "#fffdfa",
  boxShadow: "0 4px 16px rgba(20, 35, 45, 0.06)",
};

function getProjectCategory(employee) {
  const skill = String(employee.primary_skill || "").toLowerCase();
  if (["python", "machine learning", "data engineering", "sql"].includes(skill)) {
    return "Data and AI Projects";
  }
  if (["azure", "aws", "gcp", "devops"].includes(skill)) {
    return "Cloud Transformation";
  }
  if (["react", "java"].includes(skill)) {
    return "Application Modernization";
  }
  return "General Delivery";
}

function compareValues(a, b, direction) {
  const x = typeof a === "number" ? a : String(a || "").toLowerCase();
  const y = typeof b === "number" ? b : String(b || "").toLowerCase();
  if (x < y) return direction === "asc" ? -1 : 1;
  if (x > y) return direction === "asc" ? 1 : -1;
  return 0;
}

export default function EmployeesPage({ role, onBackToDashboard, onLogout }) {
  const [employees, setEmployees] = useState([]);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState("name");
  const [sortDirection, setSortDirection] = useState("asc");
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [activeTab, setActiveTab] = useState("employees");
  const [projectView, setProjectView] = useState("list");
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [selectedProjectDetails, setSelectedProjectDetails] = useState(null);
  const [projectLoading, setProjectLoading] = useState(false);
  const [assigningEmployeeId, setAssigningEmployeeId] = useState("");
  const [unassigningEmployeeId, setUnassigningEmployeeId] = useState("");
  const [aiPrompt, setAiPrompt] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiRecommendation, setAiRecommendation] = useState(null);
  const isViewer = role === "viewer";
  const canManage = role === "admin" || role === "manager";

  const loadEmployeesAndProjects = async () => {
    const [employeeData, projectData] = await Promise.all([getEmployees(500), getProjects(500)]);
    setEmployees(Array.isArray(employeeData) ? employeeData : []);
    setProjects(Array.isArray(projectData) ? projectData : []);
  };

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        await loadEmployeesAndProjects();
      } catch (err) {
        const message = err?.response?.data?.detail || err?.message || "Failed to load employees.";
        setError(message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const rows = useMemo(() => {
    const normalized = employees.map((employee) => ({
      ...employee,
      project_category: getProjectCategory(employee),
    }));

    const q = query.trim().toLowerCase();
    const filtered = q
      ? normalized.filter((employee) =>
          [
            employee.employee_id,
            employee.name,
            employee.primary_skill,
            employee.secondary_skill,
            employee.role,
            employee.availability_status,
            employee.project_category,
            employee.latest_project_name,
            employee.latest_project_domain,
            employee.location,
          ]
            .join(" ")
            .toLowerCase()
            .includes(q)
        )
      : normalized;

    return [...filtered].sort((a, b) => compareValues(a[sortKey], b[sortKey], sortDirection));
  }, [employees, query, sortKey, sortDirection]);

  const filteredProjects = useMemo(() => {
    const q = query.trim().toLowerCase();
    const base = q
      ? projects.filter((project) =>
          [
            project.project_id,
            project.project_name,
            project.domain,
            project.location,
            ...(project.required_skills || []),
          ]
            .join(" ")
            .toLowerCase()
            .includes(q)
        )
      : projects;

    return [...base].sort((a, b) => compareValues(a[sortKey], b[sortKey], sortDirection));
  }, [projects, query, sortKey, sortDirection]);

  const pagedProjects = useMemo(() => {
    const start = page * rowsPerPage;
    return filteredProjects.slice(start, start + rowsPerPage);
  }, [filteredProjects, page, rowsPerPage]);

  const pagedRows = useMemo(() => {
    const start = page * rowsPerPage;
    return rows.slice(start, start + rowsPerPage);
  }, [rows, page, rowsPerPage]);

  const handleChangePage = (_event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
      return;
    }
    setSortKey(key);
    setSortDirection("asc");
  };

  const handleTabChange = (_event, value) => {
    setActiveTab(value);
    setProjectView("list");
    setSelectedProjectDetails(null);
    setQuery("");
    setSortDirection("asc");
    setPage(0);
    setSortKey(value === "employees" ? "name" : "project_name");
  };

  const handleViewProjectDetails = async (projectId) => {
    setProjectLoading(true);
    setError("");
    setSuccess("");
    setAiRecommendation(null);
    setAiPrompt("");
    try {
      const details = await getProjectDetails(projectId);
      if (details?.detail === "Project not found") {
        setError("Project not found.");
        setSelectedProjectDetails(null);
      } else {
        setSelectedProjectDetails(details);
        setProjectView("details");
      }
    } catch (err) {
      const message = err?.response?.data?.detail || err?.message || "Failed to load project details.";
      setError(message);
    } finally {
      setProjectLoading(false);
    }
  };

  const handleAssignEmployee = async (projectId, employeeId) => {
    setAssigningEmployeeId(employeeId);
    setError("");
    setSuccess("");
    try {
      const result = await assignEmployeeToProject(projectId, {
        employee_id: employeeId,
        allocation_percentage: 100,
      });
      if (result?.status === "exists") {
        setSuccess("Employee is already allocated to this project.");
      } else {
        setSuccess("Employee assigned successfully.");
      }

      await loadEmployeesAndProjects();
      const details = await getProjectDetails(projectId);
      setSelectedProjectDetails(details);
    } catch (err) {
      const message = err?.response?.data?.detail || err?.message || "Failed to assign employee.";
      setError(message);
    } finally {
      setAssigningEmployeeId("");
    }
  };

  const handleUnassignEmployee = async (projectId, employeeId) => {
    setUnassigningEmployeeId(employeeId);
    setError("");
    setSuccess("");
    try {
      const result = await unassignEmployeeFromProject(projectId, {
        employee_id: employeeId,
      });
      if (result?.status === "not_allocated") {
        setSuccess("Employee is already unallocated from this project.");
      } else {
        setSuccess("Employee unassigned successfully.");
      }

      await loadEmployeesAndProjects();
      const details = await getProjectDetails(projectId);
      setSelectedProjectDetails(details);
    } catch (err) {
      const message = err?.response?.data?.detail || err?.message || "Failed to unassign employee.";
      setError(message);
    } finally {
      setUnassigningEmployeeId("");
    }
  };

  const handleAskProjectAi = async () => {
    const projectId = selectedProjectDetails?.project?.project_id;
    if (!projectId) {
      return;
    }

    setAiLoading(true);
    setError("");
    try {
      const response = await getProjectAiRecommendations(projectId, {
        query: aiPrompt,
        top_k: 5,
      });
      setAiRecommendation(response);
    } catch (err) {
      const message = err?.response?.data?.detail || err?.message || "Failed to fetch AI recommendations.";
      setError(message);
    } finally {
      setAiLoading(false);
    }
  };

  const handleBackToProjectsList = () => {
    setProjectView("list");
    setProjectLoading(false);
    setAiLoading(false);
    setAiRecommendation(null);
    setAiPrompt("");
  };

  useEffect(() => {
    setPage(0);
  }, [query, sortKey, sortDirection, activeTab]);

  return (
    <Box sx={{ minHeight: "100vh", background: "linear-gradient(180deg, #f5f2eb 0%, #fefdfb 100%)", py: 5 }}>
      <Container maxWidth={false} sx={{ px: { xs: 2, sm: 3, md: 4, lg: 6, xl: 8 }, maxWidth: 1840, mx: "auto" }}>
        <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" alignItems={{ xs: "start", md: "center" }} spacing={2} sx={{ mb: 3 }}>
          <Box>
            <Typography variant="h3" sx={{ fontWeight: 800, color: "#1e2a33", mb: 1 }}>
              Workforce Directory
            </Typography>
            <Typography variant="body1" sx={{ color: "#415564" }}>
              Manage employees and projects in separate operational tabs.
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
            <Button variant="outlined" onClick={onBackToDashboard} sx={{ borderRadius: 2 }}>
              Back to Dashboard
            </Button>
            <Button variant="outlined" color="inherit" onClick={onLogout} sx={{ borderRadius: 2 }}>
              Logout
            </Button>
          </Stack>
        </Stack>

        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
        {isViewer && (
          <Alert severity="info" sx={{ mb: 2 }}>
            Viewer role has read-only access. Assign and unassign actions are disabled.
          </Alert>
        )}

        <Card sx={{ ...pageCardStyle, mb: 3 }}>
          <CardContent sx={{ p: 2.5 }}>
            <Tabs
              value={activeTab}
              onChange={handleTabChange}
              sx={{
                mb: 2,
                "& .MuiTab-root": { fontWeight: 700 },
                "& .Mui-selected": { color: "#1f6b75 !important" },
                "& .MuiTabs-indicator": { backgroundColor: "#1f6b75" },
              }}
            >
              <Tab value="employees" label="Employees" />
              <Tab value="projects" label="Projects" />
            </Tabs>

            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
              <TextField
                fullWidth
                label={activeTab === "employees" ? "Search by ID, name, skill, role" : "Search by project, domain, required skill"}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
              <FormControl sx={{ minWidth: { xs: "100%", md: 260 } }}>
                <InputLabel id="sort-by-label">Sort by</InputLabel>
                <Select
                  labelId="sort-by-label"
                  value={sortKey}
                  label="Sort by"
                  onChange={(event) => setSortKey(event.target.value)}
                >
                  {activeTab === "employees" ? (
                    [
                      <MenuItem key="project_category" value="project_category">Project Category</MenuItem>,
                      <MenuItem key="latest_project_name" value="latest_project_name">Latest Project</MenuItem>,
                      <MenuItem key="latest_project_domain" value="latest_project_domain">Latest Project Domain</MenuItem>,
                      <MenuItem key="name" value="name">Name</MenuItem>,
                      <MenuItem key="employee_id" value="employee_id">Employee ID</MenuItem>,
                      <MenuItem key="primary_skill" value="primary_skill">Primary Skill</MenuItem>,
                      <MenuItem key="years_experience" value="years_experience">Years Experience</MenuItem>,
                      <MenuItem key="current_utilization" value="current_utilization">Current Utilization</MenuItem>,
                      <MenuItem key="availability_status" value="availability_status">Availability</MenuItem>,
                    ]
                  ) : (
                    [
                      <MenuItem key="project_name" value="project_name">Project Name</MenuItem>,
                      <MenuItem key="required_headcount" value="required_headcount">Headcount</MenuItem>,
                      <MenuItem key="allocated_count" value="allocated_count">Allocated Count</MenuItem>,
                      <MenuItem key="domain" value="domain">Domain</MenuItem>,
                      <MenuItem key="location" value="location">Location</MenuItem>,
                    ]
                  )}
                </Select>
              </FormControl>
              <FormControl sx={{ minWidth: { xs: "100%", md: 180 } }}>
                <InputLabel id="direction-label">Direction</InputLabel>
                <Select
                  labelId="direction-label"
                  value={sortDirection}
                  label="Direction"
                  onChange={(event) => setSortDirection(event.target.value)}
                >
                  <MenuItem value="asc">Ascending</MenuItem>
                  <MenuItem value="desc">Descending</MenuItem>
                </Select>
              </FormControl>
            </Stack>
          </CardContent>
        </Card>

        <Card sx={pageCardStyle}>
          <CardContent sx={{ p: 0 }}>
            {loading ? (
              <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
                <CircularProgress />
              </Box>
            ) : (
              <>
                {activeTab === "employees" ? (
                  <>
                    <Box sx={{ px: 2.5, py: 2 }}>
                      <Typography variant="subtitle2" sx={{ color: "#4f5e68" }}>
                        Showing {rows.length} employees
                      </Typography>
                    </Box>
                    {selectedEmployee && (
                      <Box sx={{ px: 2.5, pb: 2 }}>
                        <Card sx={{ border: "1px solid #d8ecf1", background: "#f8fdff" }}>
                          <CardContent>
                            <Typography variant="h6" sx={{ fontWeight: 700, color: "#1e3b4a", mb: 0.5 }}>
                              Selected Employee: {selectedEmployee.name} ({selectedEmployee.employee_id})
                            </Typography>
                            <Typography variant="body2" sx={{ color: "#4a6371", mb: 1.2 }}>
                              {selectedEmployee.role} | {selectedEmployee.primary_skill} / {selectedEmployee.secondary_skill}
                            </Typography>
                            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
                              <Typography variant="body2"><strong>Experience:</strong> {selectedEmployee.years_experience} years</Typography>
                              <Typography variant="body2"><strong>Availability:</strong> {selectedEmployee.availability_status}</Typography>
                              <Typography variant="body2"><strong>Utilization:</strong> {selectedEmployee.current_utilization}%</Typography>
                            </Stack>
                            <Typography variant="body2" sx={{ mt: 1 }}><strong>Latest Project:</strong> {selectedEmployee.latest_project_name || "-"}</Typography>
                            <Typography variant="body2" sx={{ mt: 0.5 }}><strong>Project Domain:</strong> {selectedEmployee.latest_project_domain || "-"}</Typography>
                            <Typography variant="body2" sx={{ mt: 0.5 }}><strong>Certifications:</strong> {selectedEmployee.certifications || "-"}</Typography>
                            <Typography variant="body2" sx={{ mt: 1 }}><strong>Resume Summary:</strong> {selectedEmployee.resume_text || "-"}</Typography>
                          </CardContent>
                        </Card>
                      </Box>
                    )}
                    <TableContainer component={Paper} elevation={0} sx={{ borderRadius: 0 }}>
                      <Table stickyHeader size="small">
                        <TableHead>
                          <TableRow sx={{
                            "& .MuiTableCell-root": {
                              backgroundColor: "#20323f",
                              color: "#f8fafc",
                              fontWeight: 700,
                              letterSpacing: 0.3,
                              borderBottom: "2px solid #162732",
                              whiteSpace: "nowrap",
                            },
                            "& .MuiTableSortLabel-root": { color: "#f8fafc" },
                            "& .MuiTableSortLabel-icon": { color: "#f8fafc !important" },
                          }}>
                            <TableCell>
                              <TableSortLabel active={sortKey === "employee_id"} direction={sortDirection} onClick={() => handleSort("employee_id")}>Employee ID</TableSortLabel>
                            </TableCell>
                            <TableCell>
                              <TableSortLabel active={sortKey === "name"} direction={sortDirection} onClick={() => handleSort("name")}>Name</TableSortLabel>
                            </TableCell>
                            <TableCell>
                              <TableSortLabel active={sortKey === "project_category"} direction={sortDirection} onClick={() => handleSort("project_category")}>Project Category</TableSortLabel>
                            </TableCell>
                            <TableCell>
                              <TableSortLabel active={sortKey === "latest_project_name"} direction={sortDirection} onClick={() => handleSort("latest_project_name")}>Latest Project</TableSortLabel>
                            </TableCell>
                            <TableCell>
                              <TableSortLabel active={sortKey === "latest_project_domain"} direction={sortDirection} onClick={() => handleSort("latest_project_domain")}>Project Domain</TableSortLabel>
                            </TableCell>
                            <TableCell>
                              <TableSortLabel active={sortKey === "primary_skill"} direction={sortDirection} onClick={() => handleSort("primary_skill")}>Primary Skill</TableSortLabel>
                            </TableCell>
                            <TableCell>Secondary Skill</TableCell>
                            <TableCell>
                              <TableSortLabel active={sortKey === "years_experience"} direction={sortDirection} onClick={() => handleSort("years_experience")}>Experience</TableSortLabel>
                            </TableCell>
                            <TableCell>Certifications</TableCell>
                            <TableCell>
                              <TableSortLabel active={sortKey === "availability_status"} direction={sortDirection} onClick={() => handleSort("availability_status")}>Availability</TableSortLabel>
                            </TableCell>
                            <TableCell>
                              <TableSortLabel active={sortKey === "current_utilization"} direction={sortDirection} onClick={() => handleSort("current_utilization")}>Utilization</TableSortLabel>
                            </TableCell>
                            <TableCell>
                              <TableSortLabel active={sortKey === "role"} direction={sortDirection} onClick={() => handleSort("role")}>Role</TableSortLabel>
                            </TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {pagedRows.map((employee, index) => (
                            <TableRow
                              key={employee.employee_id}
                              hover
                              onClick={() => setSelectedEmployee(employee)}
                              sx={{
                                backgroundColor: index % 2 === 0 ? "#fffdfa" : "#f8f4ee",
                                cursor: "pointer",
                                "& .MuiTableCell-root": {
                                  borderBottom: "1px solid #eadfce",
                                  color: "#253744",
                                  fontSize: 13,
                                  verticalAlign: "top",
                                },
                              }}
                            >
                              <TableCell>{employee.employee_id}</TableCell>
                              <TableCell>{employee.name}</TableCell>
                              <TableCell>{employee.project_category}</TableCell>
                              <TableCell>{employee.latest_project_name || "-"}</TableCell>
                              <TableCell>{employee.latest_project_domain || "-"}</TableCell>
                              <TableCell>{employee.primary_skill}</TableCell>
                              <TableCell>{employee.secondary_skill}</TableCell>
                              <TableCell>{employee.years_experience}</TableCell>
                              <TableCell>{employee.certifications}</TableCell>
                              <TableCell>{employee.availability_status}</TableCell>
                              <TableCell>{employee.current_utilization}%</TableCell>
                              <TableCell>{employee.role}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                    <TablePagination
                      component="div"
                      count={rows.length}
                      page={page}
                      onPageChange={handleChangePage}
                      rowsPerPage={rowsPerPage}
                      onRowsPerPageChange={handleChangeRowsPerPage}
                      rowsPerPageOptions={[10, 25, 50, 100]}
                      sx={{
                        borderTop: "1px solid #eadfce",
                        backgroundColor: "#fff9f0",
                      }}
                    />
                  </>
                ) : (
                  <>
                    {projectView === "list" ? (
                      <>
                        <Box sx={{ px: 2.5, py: 2 }}>
                          <Typography variant="subtitle2" sx={{ color: "#4f5e68" }}>
                            Showing {filteredProjects.length} projects
                          </Typography>
                        </Box>
                        <TableContainer component={Paper} elevation={0} sx={{ borderRadius: 0 }}>
                          <Table stickyHeader size="small">
                            <TableHead>
                              <TableRow sx={{
                                "& .MuiTableCell-root": {
                                  backgroundColor: "#20323f",
                                  color: "#f8fafc",
                                  fontWeight: 700,
                                  letterSpacing: 0.3,
                                  borderBottom: "2px solid #162732",
                                  whiteSpace: "nowrap",
                                },
                                "& .MuiTableSortLabel-root": { color: "#f8fafc" },
                                "& .MuiTableSortLabel-icon": { color: "#f8fafc !important" },
                              }}>
                                <TableCell>Project ID</TableCell>
                                <TableCell>
                                  <TableSortLabel active={sortKey === "project_name"} direction={sortDirection} onClick={() => handleSort("project_name")}>Project Name</TableSortLabel>
                                </TableCell>
                                <TableCell>Required Skills</TableCell>
                                <TableCell>
                                  <TableSortLabel active={sortKey === "required_headcount"} direction={sortDirection} onClick={() => handleSort("required_headcount")}>Headcount</TableSortLabel>
                                </TableCell>
                                <TableCell>
                                  <TableSortLabel active={sortKey === "allocated_count"} direction={sortDirection} onClick={() => handleSort("allocated_count")}>Allocated</TableSortLabel>
                                </TableCell>
                                <TableCell>
                                  <TableSortLabel active={sortKey === "domain"} direction={sortDirection} onClick={() => handleSort("domain")}>Domain</TableSortLabel>
                                </TableCell>
                                <TableCell>
                                  <TableSortLabel active={sortKey === "location"} direction={sortDirection} onClick={() => handleSort("location")}>Location</TableSortLabel>
                                </TableCell>
                                <TableCell>Action</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {pagedProjects.map((project, index) => (
                                <TableRow
                                  key={project.project_id}
                                  hover
                                  sx={{
                                    backgroundColor: index % 2 === 0 ? "#fffdfa" : "#f8f4ee",
                                    "& .MuiTableCell-root": {
                                      borderBottom: "1px solid #eadfce",
                                      color: "#253744",
                                      fontSize: 13,
                                      verticalAlign: "top",
                                    },
                                  }}
                                >
                                  <TableCell>{project.project_id}</TableCell>
                                  <TableCell>{project.project_name}</TableCell>
                                  <TableCell>{(project.required_skills || []).join(", ") || "-"}</TableCell>
                                  <TableCell>{project.required_headcount}</TableCell>
                                  <TableCell>{project.allocated_count}</TableCell>
                                  <TableCell>{project.domain}</TableCell>
                                  <TableCell>{project.location}</TableCell>
                                  <TableCell>
                                    <Button size="small" variant="outlined" onClick={() => handleViewProjectDetails(project.project_id)}>
                                      View Details
                                    </Button>
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                        <TablePagination
                          component="div"
                          count={filteredProjects.length}
                          page={page}
                          onPageChange={handleChangePage}
                          rowsPerPage={rowsPerPage}
                          onRowsPerPageChange={handleChangeRowsPerPage}
                          rowsPerPageOptions={[10, 25, 50, 100]}
                          sx={{
                            borderTop: "1px solid #eadfce",
                            backgroundColor: "#fff9f0",
                          }}
                        />
                      </>
                    ) : (
                      <Box sx={{ p: 2.5 }}>
                        <Box sx={{ mb: 2 }}>
                          <Button variant="outlined" onClick={handleBackToProjectsList}>
                            Back to Projects
                          </Button>
                        </Box>

                        {projectLoading && (
                          <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
                            <CircularProgress />
                          </Box>
                        )}

                        {selectedProjectDetails?.project && !projectLoading && (
                          <>
                            <Card sx={{ border: "1px solid #d7d0c5", mb: 2 }}>
                              <CardContent>
                                <Typography variant="h6" sx={{ fontWeight: 700, color: "#243542", mb: 1 }}>
                                  AI Recommendation Chat (Cross-Project)
                                </Typography>
                                <Typography variant="body2" sx={{ color: "#5a6f7b", mb: 1.5 }}>
                                  Ask AI to suggest employees currently allocated to other projects who could be moved here.
                                </Typography>
                                <Stack spacing={1.2}>
                                  <TextField
                                    fullWidth
                                    multiline
                                    minRows={2}
                                    value={aiPrompt}
                                    onChange={(event) => setAiPrompt(event.target.value)}
                                    placeholder="Example: Suggest top 3 employees to move with minimal delivery risk."
                                  />
                                  <Box>
                                    <Button
                                      variant="contained"
                                      onClick={handleAskProjectAi}
                                      disabled={aiLoading}
                                      sx={{ background: "#334f67" }}
                                    >
                                      {aiLoading ? "Generating..." : "Ask AI"}
                                    </Button>
                                  </Box>

                                  {aiRecommendation?.answer && (
                                    <Box sx={{ p: 1.5, borderRadius: 1.5, border: "1px solid #d8e2ea", background: "#f7fbff" }}>
                                      <Typography variant="subtitle2" sx={{ fontWeight: 700, color: "#1f3a51", mb: 0.6 }}>
                                        AI Response
                                      </Typography>
                                      <Typography variant="body2" sx={{ whiteSpace: "pre-wrap", color: "#2a3f4e" }}>
                                        {aiRecommendation.answer}
                                      </Typography>
                                    </Box>
                                  )}

                                  {Array.isArray(aiRecommendation?.suggestions) && aiRecommendation.suggestions.length > 0 && (
                                    <Box sx={{ p: 1.5, borderRadius: 1.5, border: "1px solid #e3ddd3" }}>
                                      <Typography variant="subtitle2" sx={{ fontWeight: 700, color: "#243542", mb: 1 }}>
                                        Suggested Employees From Other Projects
                                      </Typography>
                                      <Stack spacing={0.8}>
                                        {aiRecommendation.suggestions.map((candidate) => (
                                          <Box key={`cross-${candidate.employee_id}-${candidate.source_project_id}`} sx={{ border: "1px solid #ece7de", borderRadius: 1.2, p: 1 }}>
                                            <Typography variant="body2" sx={{ fontWeight: 700 }}>
                                              {candidate.name} ({candidate.employee_id})
                                            </Typography>
                                            <Typography variant="caption" sx={{ color: "#60727d", display: "block" }}>
                                              Source: {candidate.source_project_name} ({candidate.source_project_id}) | Allocation {candidate.source_allocation_percentage}%
                                            </Typography>
                                            <Typography variant="caption" sx={{ color: "#60727d", display: "block" }}>
                                              {candidate.primary_skill} / {candidate.secondary_skill} | {candidate.years_experience} years | Utilization {candidate.current_utilization}%
                                            </Typography>
                                            <Typography variant="caption" sx={{ color: "#1f6b75" }}>
                                              Matched skills: {(candidate.matched_skills || []).join(", ")}
                                            </Typography>
                                          </Box>
                                        ))}
                                      </Stack>
                                    </Box>
                                  )}
                                </Stack>
                              </CardContent>
                            </Card>

                        <Card sx={{ border: "1px solid #d7d0c5", mb: 2 }}>
                          <CardContent>
                            <Typography variant="h6" sx={{ fontWeight: 700, color: "#243542" }}>
                              {selectedProjectDetails.project.project_name}
                            </Typography>
                            <Typography variant="body2" sx={{ mt: 0.5, color: "#5a6f7b" }}>
                              {selectedProjectDetails.project.project_id} | {selectedProjectDetails.project.domain} | {selectedProjectDetails.project.location}
                            </Typography>
                            <Typography variant="body2" sx={{ mt: 1 }}>
                              Requires {selectedProjectDetails.project.required_headcount} members with minimum {selectedProjectDetails.project.min_experience} years experience.
                            </Typography>
                            <Typography variant="body2" sx={{ mt: 0.5 }}>
                              Skills required: {(selectedProjectDetails.project.required_skills || []).join(", ") || "-"}
                            </Typography>
                          </CardContent>
                        </Card>

                        <Card sx={{ border: "1px solid #d7d0c5", mb: 2 }}>
                          <CardContent>
                            <Typography variant="h6" sx={{ fontWeight: 700, color: "#243542", mb: 1.2 }}>
                              Allocated Members
                            </Typography>
                            {selectedProjectDetails.allocated_members?.length ? (
                              <Stack spacing={1}>
                                {selectedProjectDetails.allocated_members.map((member) => (
                                  <Box key={`${selectedProjectDetails.project.project_id}-${member.employee_id}`} sx={{ p: 1.2, border: "1px solid #e3ddd3", borderRadius: 1.5 }}>
                                    <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" spacing={1}>
                                      <Box>
                                        <Typography variant="body2" sx={{ fontWeight: 700 }}>{member.name} ({member.employee_id})</Typography>
                                        <Typography variant="caption" sx={{ color: "#60727d" }}>
                                          {member.primary_skill} | {member.role} | {member.allocation_percentage}% allocated
                                        </Typography>
                                      </Box>
                                      <Button
                                        size="small"
                                        color="error"
                                        variant="outlined"
                                        onClick={() => handleUnassignEmployee(selectedProjectDetails.project.project_id, member.employee_id)}
                                        disabled={!canManage || unassigningEmployeeId === member.employee_id || assigningEmployeeId === member.employee_id}
                                        sx={{ minWidth: 110 }}
                                      >
                                        {unassigningEmployeeId === member.employee_id ? "Unassigning..." : "Unassign"}
                                      </Button>
                                    </Stack>
                                  </Box>
                                ))}
                              </Stack>
                            ) : (
                              <Typography variant="body2" sx={{ color: "#60727d" }}>No members allocated yet.</Typography>
                            )}
                          </CardContent>
                        </Card>

                        <Card sx={{ border: "1px solid #d7d0c5" }}>
                          <CardContent>
                            <Typography variant="h6" sx={{ fontWeight: 700, color: "#243542", mb: 1.2 }}>
                              Fit Candidates (Available)
                            </Typography>
                            {selectedProjectDetails.fit_candidates?.length ? (
                              <Stack spacing={1}>
                                {selectedProjectDetails.fit_candidates.map((candidate) => (
                                  <Box key={`${selectedProjectDetails.project.project_id}-${candidate.employee_id}`} sx={{ p: 1.2, border: "1px solid #e3ddd3", borderRadius: 1.5 }}>
                                    <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" spacing={1}>
                                      <Box>
                                        <Typography variant="body2" sx={{ fontWeight: 700 }}>{candidate.name} ({candidate.employee_id})</Typography>
                                        <Typography variant="caption" sx={{ color: "#60727d", display: "block" }}>
                                          {candidate.primary_skill} / {candidate.secondary_skill} | {candidate.years_experience} years | Utilization {candidate.current_utilization}%
                                        </Typography>
                                        <Typography variant="caption" sx={{ color: "#1f6b75" }}>
                                          Matched skills: {(candidate.matched_skills || []).join(", ")}
                                        </Typography>
                                      </Box>
                                      <Button
                                        size="small"
                                        variant="contained"
                                        onClick={() => handleAssignEmployee(selectedProjectDetails.project.project_id, candidate.employee_id)}
                                        disabled={!canManage || assigningEmployeeId === candidate.employee_id}
                                        sx={{ background: "#1f6b75", minWidth: 110 }}
                                      >
                                        {assigningEmployeeId === candidate.employee_id ? "Assigning..." : "Assign"}
                                      </Button>
                                    </Stack>
                                  </Box>
                                ))}
                              </Stack>
                            ) : (
                              <Typography variant="body2" sx={{ color: "#60727d" }}>
                                No available fit candidates currently meet this project's criteria.
                              </Typography>
                            )}
                          </CardContent>
                        </Card>
                          </>
                        )}
                      </Box>
                    )}
                  </>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
}
