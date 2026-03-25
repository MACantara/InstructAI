/**
 * Renders a university-style syllabus from the structured JSON response.
 * Includes CLO-PLO Alignment Matrix, LLOs per lesson, and LLO-CLO Alignment Matrix.
 */
export const renderSyllabus = (response) => {
    if (!response || !response.raw_json) {
        return `<div class="alert alert-warning">No syllabus data available.</div>`;
    }

    const json = response.raw_json;
    const topics = Array.isArray(json.weeklyTopics) ? json.weeklyTopics : [];
    const clos = Array.isArray(json.courseLearningOutcomes) ? json.courseLearningOutcomes : [];
    const plos = Array.isArray(json.programOutcomes) ? json.programOutcomes : [];

    return `
        <div class="syllabus-wrapper">

            <!-- Header -->
            <div class="syllabus-header text-center mb-4">
                <h1 class="h2 text-primary fw-bold">${json.title || 'Untitled Course'}</h1>
                <p class="text-muted mb-0">${json.courseDescription || ''}</p>
            </div>

            <!-- Course Info Cards -->
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

            <!-- Programme Learning Outcomes -->
            ${renderPLOs(plos)}

            <!-- Course Learning Outcomes + CLO-PLO Matrix -->
            ${renderCLOs(clos, plos)}

            <!-- Course Schedule Table -->
            <div class="card border-0 shadow-sm mb-4">
                <div class="card-header bg-primary text-white py-3">
                    <h2 class="h5 mb-0"><i class="fas fa-table me-2"></i>Course Schedule</h2>
                </div>
                <div class="table-responsive">
                    <table class="table table-bordered syllabus-table mb-0 align-top">
                        <thead class="table-dark">
                            <tr>
                                <th class="col-week text-center">Week</th>
                                <th class="col-timeframe">Time Frame</th>
                                <th class="col-topics">Topics &amp; Subtopics</th>
                                <th class="col-llo">Lesson Learning<br>Outcomes (LLOs)</th>
                                <th class="col-clo text-center">CLO</th>
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

            <!-- LLO-CLO Alignment Matrix -->
            ${renderLLOCLOMatrix(topics, clos)}

        </div>
    `;
};

/* ─────────────────────────────────────────────
   Programme Learning Outcomes
───────────────────────────────────────────── */
const renderPLOs = (plos) => {
    if (!plos.length) return '';
    return `
        <div class="card border-0 shadow-sm mb-3">
            <div class="card-header bg-dark text-white py-2">
                <h2 class="h6 mb-0 text-uppercase">
                    <i class="fas fa-university me-2"></i>Programme Learning Outcomes (PLOs)
                </h2>
            </div>
            <div class="card-body py-3">
                <div class="row g-2">
                    ${plos.map(plo => `
                        <div class="col-md-6">
                            <div class="border rounded p-2 h-100 bg-light">
                                <div class="mb-2">
                                    <label class="form-label form-label-sm small text-muted mb-1">PLO ID</label>
                                    <input type="text" class="form-control form-control-sm plo-editor-id" value="${plo.id || ''}" readonly>
                                </div>
                                <div>
                                    <label class="form-label form-label-sm small text-muted mb-1">Description (Editable)</label>
                                    <textarea class="form-control form-control-sm plo-editor-text" rows="2">${plo.description || ''}</textarea>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
};

/* ─────────────────────────────────────────────
   Course Learning Outcomes + CLO-PLO Matrix
───────────────────────────────────────────── */
const renderCLOs = (clos, plos) => {
    if (!clos.length) return '';

    const ploIds = plos.map(p => p.id);

    const cloListHtml = clos.map(clo => {
        const plosHtml = (clo.ploAlignment || [])
            .map(pid => `<span class="badge bg-secondary plo-badge ms-1">${pid}</span>`)
            .join('');
        return `
            <div class="col-md-6">
                <div class="d-flex align-items-start">
                    <span class="badge bg-primary me-2 mt-1 flex-shrink-0 clo-badge">${clo.id}</span>
                    <div>
                        <span class="small">${clo.description}</span>
                        <div class="mt-1">${plosHtml}</div>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    // CLO-PLO Matrix
    const matrixRowsHtml = clos.map(clo => {
        const aligned = new Set(clo.ploAlignment || []);
        const cells = ploIds.map(pid =>
            `<td class="text-center ${aligned.has(pid) ? 'matrix-hit' : 'matrix-miss'}">
                ${aligned.has(pid) ? '<i class="fas fa-check text-success"></i>' : ''}
            </td>`
        ).join('');
        return `<tr>
            <td><span class="badge bg-primary clo-badge">${clo.id}</span></td>
            ${cells}
        </tr>`;
    }).join('');

    const matrixHeaderCells = ploIds.map(pid =>
        `<th class="text-center small">${pid}</th>`
    ).join('');

    return `
        <div class="card border-0 shadow-sm mb-3">
            <div class="card-header bg-secondary text-white py-2">
                <h2 class="h6 mb-0 text-uppercase">
                    <i class="fas fa-bullseye me-2"></i>Course Learning Outcomes (CLOs)
                </h2>
            </div>
            <div class="card-body py-3">
                <div class="row g-2 mb-4">${cloListHtml}</div>

                <!-- CLO-PLO Alignment Matrix -->
                <h3 class="h6 fw-semibold mb-2 text-secondary">
                    <i class="fas fa-th me-1"></i>CLO-PLO Alignment Matrix
                </h3>
                <div class="table-responsive">
                    <table class="table table-bordered table-sm alignment-matrix mb-0">
                        <thead class="table-secondary">
                            <tr>
                                <th class="small">CLO \\ PLO</th>
                                ${matrixHeaderCells}
                            </tr>
                        </thead>
                        <tbody>${matrixRowsHtml}</tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
};

/* ─────────────────────────────────────────────
   Single schedule row
───────────────────────────────────────────── */
const renderSyllabusRow = (entry, idx) => {
    const rowClass = idx % 2 === 0 ? '' : 'table-light';

    const subtopicsHtml = (entry.subtopics || []).length
        ? `<ul class="mb-0 ps-3 subtopics-list">${entry.subtopics.map(s => `<li>${s}</li>`).join('')}</ul>`
        : '';

    const lloHtml = (entry.lessonLearningOutcomes || []).map(llo => {
        const cloBadges = (llo.cloAlignment || [])
            .map(c => `<span class="badge bg-primary llo-clo-badge">${c}</span>`)
            .join('');
        return `<div class="llo-item mb-1">
            <span class="llo-id">${llo.id}</span>
            <span class="small text-muted">${llo.description}</span>
            <div class="mt-1">${cloBadges}</div>
        </div>`;
    }).join('') || '—';

    const cloHtml = (entry.cloAlignment || []).map(c =>
        `<span class="badge bg-primary co-badge">${c}</span>`
    ).join('') || '—';

    const activitiesHtml = (entry.learningActivities || []).length
        ? `<ul class="mb-0 ps-3">${entry.learningActivities.map(a => `<li>${a}</li>`).join('')}</ul>`
        : '—';

    const assessmentHtml = (entry.assessmentStrategies || []).length
        ? `<ul class="mb-0 ps-3">${entry.assessmentStrategies.map(s => `<li>${s}</li>`).join('')}</ul>`
        : '—';

    return `
        <tr class="${rowClass}">
            <td class="text-center fw-bold week-cell">
                <span class="badge bg-secondary week-badge">Week ${entry.weekRange}</span>
            </td>
            <td class="timeframe-cell small">
                <span class="badge bg-primary-subtle text-primary timeframe-item">Lecture: 3 hours</span>
                <span class="badge bg-success-subtle text-success timeframe-item">Laboratory: 2 hours</span>
            </td>
            <td>
                <div class="fw-semibold mb-1">${entry.mainTopic}</div>
                ${subtopicsHtml}
            </td>
            <td class="llo-cell">${lloHtml}</td>
            <td class="text-center co-cell">${cloHtml}</td>
            <td class="kpi-cell small">${entry.kpi || '—'}</td>
            <td class="small">${activitiesHtml}</td>
            <td class="small">${assessmentHtml}</td>
        </tr>
    `;
};

/* ─────────────────────────────────────────────
   LLO-CLO Alignment Matrix (aggregate)
───────────────────────────────────────────── */
const renderLLOCLOMatrix = (topics, clos) => {
    if (!clos.length || !topics.length) return '';

    // Collect all LLOs across all entries
    const allLLOs = [];
    topics.forEach(entry => {
        (entry.lessonLearningOutcomes || []).forEach(llo => {
            allLLOs.push({ ...llo, weekRange: entry.weekRange });
        });
    });

    if (!allLLOs.length) return '';

    const cloIds = clos.map(c => c.id);

    const headerCells = cloIds.map(cid =>
        `<th class="text-center small">${cid}</th>`
    ).join('');

    const rows = allLLOs.map(llo => {
        const aligned = new Set(llo.cloAlignment || []);
        const cells = cloIds.map(cid =>
            `<td class="text-center ${aligned.has(cid) ? 'matrix-hit' : 'matrix-miss'}">
                ${aligned.has(cid) ? '<i class="fas fa-check text-success"></i>' : ''}
            </td>`
        ).join('');
        return `<tr>
            <td>
                <span class="llo-id">${llo.id}</span>
                <span class="badge bg-secondary week-badge ms-1">Wk ${llo.weekRange}</span>
            </td>
            <td class="small text-muted">${llo.description}</td>
            ${cells}
        </tr>`;
    }).join('');

    return `
        <div class="card border-0 shadow-sm mb-4">
            <div class="card-header bg-info text-white py-2">
                <h2 class="h6 mb-0 text-uppercase">
                    <i class="fas fa-th me-2"></i>LLO-CLO Alignment Matrix
                </h2>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-bordered table-sm alignment-matrix mb-0">
                        <thead class="table-info">
                            <tr>
                                <th class="small">LLO</th>
                                <th class="small">Description</th>
                                ${headerCells}
                            </tr>
                        </thead>
                        <tbody>${rows}</tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
};
