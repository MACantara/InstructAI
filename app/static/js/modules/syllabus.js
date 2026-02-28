/**
 * Renders a university-style syllabus from the structured JSON response.
 */
export const renderSyllabus = (response) => {
    if (!response || !response.raw_json) {
        return `<div class="alert alert-warning">No syllabus data available.</div>`;
    }

    const json = response.raw_json;
    const topics = Array.isArray(json.weeklyTopics) ? json.weeklyTopics : [];

    return `
        <div class="syllabus-wrapper">

            <!-- Header -->
            <div class="syllabus-header text-center mb-4">
                <h1 class="h2 text-primary fw-bold">${json.title || 'Untitled Course'}</h1>
                <p class="text-muted mb-0">${json.courseDescription || ''}</p>
            </div>

            <!-- Course Info Row -->
            <div class="row g-3 mb-4">
                <div class="col-md-4">
                    <div class="card h-100 border-0 shadow-sm">
                        <div class="card-body">
                            <div class="d-flex align-items-center mb-1">
                                <i class="fas fa-clock text-primary me-2"></i>
                                <span class="fw-semibold small text-uppercase text-muted">Duration</span>
                            </div>
                            <p class="mb-0">${json.courseStructure?.duration || '—'}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card h-100 border-0 shadow-sm">
                        <div class="card-body">
                            <div class="d-flex align-items-center mb-1">
                                <i class="fas fa-chalkboard-teacher text-primary me-2"></i>
                                <span class="fw-semibold small text-uppercase text-muted">Format</span>
                            </div>
                            <p class="mb-0">${json.courseStructure?.format || '—'}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card h-100 border-0 shadow-sm">
                        <div class="card-body">
                            <div class="d-flex align-items-center mb-1">
                                <i class="fas fa-tasks text-primary me-2"></i>
                                <span class="fw-semibold small text-uppercase text-muted">Assessment</span>
                            </div>
                            <p class="mb-0">${json.courseStructure?.assessment || '—'}</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Course Outcomes -->
            ${renderCourseOutcomes(json.courseOutcomes)}

            <!-- Syllabus Table -->
            <div class="card border-0 shadow-sm">
                <div class="card-header bg-primary text-white py-3">
                    <h2 class="h5 mb-0"><i class="fas fa-table me-2"></i>Course Schedule</h2>
                </div>
                <div class="table-responsive">
                    <table class="table table-bordered syllabus-table mb-0 align-top">
                        <thead class="table-dark">
                            <tr>
                                <th class="col-week text-center">Week</th>
                                <th class="col-topics">Topics &amp; Subtopics</th>
                                <th class="col-co text-center">Course<br>Outcome (CO)</th>
                                <th class="col-kpi">Key Performance<br>Indicator (KPI)</th>
                                <th class="col-activities">Learning Activities /<br>Performance Task</th>
                                <th class="col-assessment">Assessment Strategies &amp; Tools /<br>Results &amp; Evidence</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${topics.map((entry, idx) => renderSyllabusRow(entry, idx)).join('')}
                        </tbody>
                    </table>
                </div>
            </div>

        </div>
    `;
};

/**
 * Renders the Course Outcomes section above the table.
 */
const renderCourseOutcomes = (outcomes) => {
    if (!Array.isArray(outcomes) || outcomes.length === 0) return '';
    return `
        <div class="card border-0 shadow-sm mb-4">
            <div class="card-header bg-secondary text-white py-2">
                <h2 class="h6 mb-0 text-uppercase letter-spacing-1">
                    <i class="fas fa-bullseye me-2"></i>Course Outcomes
                </h2>
            </div>
            <div class="card-body py-3">
                <div class="row g-2">
                    ${outcomes.map(co => `
                        <div class="col-md-4">
                            <div class="d-flex align-items-start">
                                <span class="badge bg-primary me-2 mt-1 flex-shrink-0">${co.id}</span>
                                <span class="small">${co.description}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
};

/**
 * Renders a single row of the syllabus table.
 */
const renderSyllabusRow = (entry, idx) => {
    const rowClass = idx % 2 === 0 ? '' : 'table-light';

    const subtopicsHtml = Array.isArray(entry.subtopics) && entry.subtopics.length
        ? `<ul class="mb-0 ps-3 subtopics-list">${entry.subtopics.map(s => `<li>${s}</li>`).join('')}</ul>`
        : '';

    const coHtml = Array.isArray(entry.courseOutcomes) && entry.courseOutcomes.length
        ? entry.courseOutcomes.map(co =>
            `<span class="badge bg-primary co-badge">${co}</span>`
          ).join('')
        : '—';

    const activitiesHtml = Array.isArray(entry.learningActivities) && entry.learningActivities.length
        ? `<ul class="mb-0 ps-3">${entry.learningActivities.map(a => `<li>${a}</li>`).join('')}</ul>`
        : '—';

    const assessmentHtml = Array.isArray(entry.assessmentStrategies) && entry.assessmentStrategies.length
        ? `<ul class="mb-0 ps-3">${entry.assessmentStrategies.map(s => `<li>${s}</li>`).join('')}</ul>`
        : '—';

    return `
        <tr class="${rowClass}">
            <td class="text-center fw-bold week-cell">
                <span class="badge bg-secondary week-badge">Week ${entry.weekRange}</span>
            </td>
            <td>
                <div class="fw-semibold mb-1">${entry.mainTopic}</div>
                ${subtopicsHtml}
            </td>
            <td class="text-center co-cell">${coHtml}</td>
            <td class="kpi-cell small">${entry.kpi || '—'}</td>
            <td class="small">${activitiesHtml}</td>
            <td class="small">${assessmentHtml}</td>
        </tr>
    `;
};
