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
    const peos = Array.isArray(json.programEducationalObjectives) ? json.programEducationalObjectives : [];
    const lectureHours = json.timeFramePerWeek?.lectureHours || 3;
    const labHours = json.timeFramePerWeek?.laboratoryHours || 2;

    return `
        <div class="syllabus-wrapper">

            <!-- Header -->
            <div class="syllabus-header text-center mb-4">
                <h1 class="h2 text-primary fw-bold">${json.title || 'Untitled Course'}</h1>
                <p class="mb-1 fw-semibold text-secondary">${json.courseCode || ''}</p>
                <p class="text-muted mb-0">${json.courseDescription || ''}</p>
            </div>

            <!-- Course Info Cards -->
            <div class="row g-3 mb-4">
                <div class="col-md-6">
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
                <div class="col-md-6">
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
            </div>

            <!-- Graduate Attributes -->
            ${renderGraduateAttributes(json.graduateAttributes || {})}

            <!-- Program Educational Objectives -->
            ${renderPEOs(peos)}

            <!-- Programme Learning Outcomes -->
            ${renderPLOs(plos, peos)}

            <!-- Course Learning Outcomes + CLO-PLO Matrix -->
            ${renderCLOs(clos, plos)}

            <!-- LLO-CLO Alignment Matrix -->
            ${renderLLOCLOMatrix(topics, clos)}

            <!-- Course Schedule Table -->
            <div class="card border-0 shadow-sm mb-4">
                <div class="card-header bg-primary text-white py-3">
                    <h2 class="h5 mb-0"><i class="fas fa-table me-2"></i>Course Schedule</h2>
                </div>
                <div class="table-responsive">
                    <table class="table table-bordered syllabus-table mb-0 align-top">
                        <thead class="table-dark">
                            <tr>
                                <th class="col-learning-outcomes">Learning Outcome (A, S, K)</th>
                                <th class="col-topics">Topic</th>
                                <th class="col-timeframe">Time Frame</th>
                                <th class="col-activities">Learning Activity / Performance Task</th>
                                <th class="col-assessment">Assessment Strategy and Tool</th>
                                <th class="col-results">Result &amp; Evidence</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${topics.map((entry, idx) => renderSyllabusRow(entry, idx, lectureHours, labHours)).join('')}
                        </tbody>
                    </table>
                </div>
            </div>

        </div>
    `;
};

/* ─────────────────────────────────────────────
   Graduate Attributes
───────────────────────────────────────────── */
const renderGraduateAttributes = (attributes) => {
    const sections = [
        { key: 'Character', icon: 'fa-user-shield' },
        { key: 'Competence', icon: 'fa-brain' },
        { key: 'Commitment to Service', icon: 'fa-hands-helping' }
    ];

    if (!sections.some(section => Array.isArray(attributes[section.key]) && attributes[section.key].length)) {
        return '';
    }

    return `
        <div class="card border-0 shadow-sm mb-3">
            <div class="card-header bg-success text-white py-2">
                <h2 class="h6 mb-0 text-uppercase">
                    <i class="fas fa-graduation-cap me-2"></i>Graduate Attributes
                </h2>
            </div>
            <div class="card-body py-3">
                <div class="row g-3">
                    ${sections.map(section => {
                        const items = Array.isArray(attributes[section.key]) ? attributes[section.key] : [];
                        return `
                            <div class="col-md-4">
                                <div class="border rounded p-2 h-100 bg-light">
                                    <h3 class="h6 mb-2 text-success"><i class="fas ${section.icon} me-1"></i>${section.key}</h3>
                                    <ul class="small mb-0 ps-3">
                                        ${items.map(item => `<li>${item}</li>`).join('') || '<li>—</li>'}
                                    </ul>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        </div>
    `;
};

/* ─────────────────────────────────────────────
   Program Educational Objectives
───────────────────────────────────────────── */
const renderPEOs = (peos) => {
    if (!peos.length) return '';

    return `
        <div class="card border-0 shadow-sm mb-3">
            <div class="card-header bg-warning text-dark py-2">
                <h2 class="h6 mb-0 text-uppercase">
                    <i class="fas fa-sitemap me-2"></i>Program Educational Objectives (PEOs) in Relation to Graduate Attributes
                </h2>
            </div>
            <div class="card-body py-3">
                <div class="row g-2">
                    ${peos.map(peo => `
                        <div class="col-md-6">
                            <div class="border rounded p-2 h-100 bg-light">
                                <div class="d-flex align-items-start mb-1">
                                    <span class="badge bg-warning text-dark me-2 mt-1 flex-shrink-0">${peo.id || 'PEO'}</span>
                                    <span class="small">${peo.description || '—'}</span>
                                </div>
                                <div>
                                    ${(peo.graduateAttributeAlignment || [])
                                        .map(attr => `<span class="badge bg-secondary me-1">${attr}</span>`)
                                        .join('') || '<span class="small text-muted">No alignment</span>'}
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
   Programme Learning Outcomes
───────────────────────────────────────────── */
const renderPLOs = (plos, peos) => {
    if (!plos.length) return '';
    const peoIds = (peos || []).map(peo => peo.id);

    const matrixHeader = peoIds.map(pid => `<th class="text-center small">${pid}</th>`).join('');
    const matrixRows = plos.map(plo => {
        const aligned = new Set(plo.peoAlignment || []);
        const cells = peoIds.map(pid => `
            <td class="text-center ${aligned.has(pid) ? 'matrix-hit' : 'matrix-miss'}">
                ${aligned.has(pid) ? '<i class="fas fa-check text-success"></i>' : ''}
            </td>
        `).join('');
        return `<tr><td><span class="badge bg-dark plo-badge">${plo.id || 'PLO'}</span></td>${cells}</tr>`;
    }).join('');

    return `
        <div class="card border-0 shadow-sm mb-3">
            <div class="card-header bg-dark text-white py-2">
                <h2 class="h6 mb-0 text-uppercase">
                    <i class="fas fa-university me-2"></i>Programme Learning Outcomes (PLOs) in Relation to Program Educational Outcomes (PEOs)
                </h2>
            </div>
            <div class="card-body py-3">
                <div class="row g-2">
                    ${plos.map(plo => `
                        <div class="col-md-6">
                            <div class="border rounded p-2 h-100 bg-light">
                                <div class="d-flex align-items-start mb-1">
                                    <span class="badge bg-dark me-2 mt-1 flex-shrink-0">${plo.id || 'PLO'}</span>
                                    <span class="small">${plo.description || '—'}</span>
                                </div>
                                <div class="mt-2">
                                    ${(plo.peoAlignment || [])
                                        .map(peo => `<span class="badge bg-secondary me-1">${peo}</span>`)
                                        .join('') || '<span class="small text-muted">No PEO alignment</span>'}
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>

                ${peoIds.length ? `
                <h3 class="h6 fw-semibold mt-4 mb-2 text-dark">
                    <i class="fas fa-th me-1"></i>PLO-PEO Alignment Matrix
                </h3>
                <div class="table-responsive">
                    <table class="table table-bordered table-sm alignment-matrix mb-0">
                        <thead class="table-dark">
                            <tr>
                                <th class="small">PLO \\ PEO</th>
                                ${matrixHeader}
                            </tr>
                        </thead>
                        <tbody>${matrixRows}</tbody>
                    </table>
                </div>
                ` : ''}
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
const renderSyllabusRow = (entry, idx, lectureHours, labHours) => {
    const rowClass = idx % 2 === 0 ? '' : 'table-light';

    const weekLabel = entry.weekRange ? `WEEK ${entry.weekRange}` : `WEEK ${idx + 1}`;

    const learningOutcomes = Array.isArray(entry.learningOutcomesASK) && entry.learningOutcomesASK.length
        ? entry.learningOutcomesASK
        : (entry.lessonLearningOutcomes || []).map(llo => llo.description).filter(Boolean);

    const learningOutcomesHtml = learningOutcomes.length
        ? `<ul class="mb-0 ps-3">${learningOutcomes.map(item => `<li>${item}</li>`).join('')}</ul>`
        : '—';

    const topicHtml = `
        <div class="fw-semibold mb-1">${entry.mainTopic || '—'}</div>
        ${(entry.subtopics || []).length
            ? `<ul class="mb-0 ps-3 subtopics-list">${entry.subtopics.map(s => `<li>${s}</li>`).join('')}</ul>`
            : ''}
    `;

    const timeframeItems = [
        `${lectureHours} Hours`,
        `${labHours} Hours`
    ];

    const timeframeHtml = `<ul class="mb-0 ps-3">${timeframeItems.map(t => `<li>${t}</li>`).join('')}</ul>`;

    const learningActivityHtml = (entry.learningActivities || []).length
        ? `<ul class="mb-0 ps-3">${entry.learningActivities.map(a => `<li>${a}</li>`).join('')}</ul>`
        : '—';

    const assessmentHtml = (entry.assessmentStrategies || []).length
        ? `<ul class="mb-0 ps-3">${entry.assessmentStrategies.map(s => `<li>${s}</li>`).join('')}</ul>`
        : '—';

    const resultEvidenceHtml = (entry.resultEvidence || []).length
        ? `<ul class="mb-0 ps-3">${entry.resultEvidence.map(r => `<li>${r}</li>`).join('')}</ul>`
        : '—';

    return `
        <tr class="week-header-row">
            <td colspan="6" class="fw-bold">${weekLabel}</td>
        </tr>
        <tr class="${rowClass}">
            <td class="small">${learningOutcomesHtml}</td>
            <td>${topicHtml}</td>
            <td class="timeframe-cell small">${timeframeHtml}</td>
            <td class="small">${learningActivityHtml}</td>
            <td class="small">${assessmentHtml}</td>
            <td class="small">${resultEvidenceHtml}</td>
        </tr>
    `;
};

/* ─────────────────────────────────────────────
   LLO-CLO Alignment Matrix (aggregate)
───────────────────────────────────────────── */
const renderLLOCLOMatrix = (topics, clos) => {
    if (!clos.length || !topics.length) return '';

    // Build matrix rows from generated Learning Outcome (A, S, K) per week.
    const allLLOs = [];
    topics.forEach((entry, topicIndex) => {
        const outcomes = Array.isArray(entry.learningOutcomesASK) ? entry.learningOutcomesASK : [];
        outcomes.forEach((outcome, outcomeIndex) => {
            allLLOs.push({
                id: `LO-${topicIndex + 1}.${outcomeIndex + 1}`,
                description: outcome,
                weekRange: entry.weekRange,
                cloAlignment: Array.isArray(entry.cloAlignment) ? entry.cloAlignment : []
            });
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
