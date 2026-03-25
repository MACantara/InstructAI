import { renderSyllabus } from './modules/syllabus.js';

const missionKeywords = ['A', 'B', 'C', 'D', 'E', 'F'];

let graduateAttributeRows = [
    {
        id: 'GA1',
        section: 'Character',
        description: 'Graduates demonstrate a deep faith in God, embodying professional, humanistic, and altruistic values in their personal and professional lives.',
        missionKeywordAlignment: ['B', 'C', 'F']
    },
    {
        id: 'GA2',
        section: 'Character',
        description: 'Graduates serve as Helpers of God, dedicating their knowledge and skills to the betterment of others.',
        missionKeywordAlignment: ['C', 'D', 'F']
    },
    {
        id: 'GA3',
        section: 'Character',
        description: 'Graduates exemplify servant leadership, guiding others with integrity, humility, and a commitment to the common good.',
        missionKeywordAlignment: ['A', 'D', 'F']
    },
    {
        id: 'GA4',
        section: 'Character',
        description: 'Graduates uphold ethical responsibility in both physical and digital environments, practicing responsible citizenship and promoting positive engagement and interactions.',
        missionKeywordAlignment: ['A', 'D', 'E']
    },
    {
        id: 'GA5',
        section: 'Competence',
        description: 'Graduates communicate effectively across diverse contexts, demonstrating clarity, coherence, and cultural sensitivity.',
        missionKeywordAlignment: ['A', 'B', 'C', 'D', 'E', 'F']
    },
    {
        id: 'GA6',
        section: 'Competence',
        description: 'Graduates apply critical and creative thinking to solve complex problems and innovate in their respective fields.',
        missionKeywordAlignment: ['B', 'E', 'F']
    },
    {
        id: 'GA7',
        section: 'Competence',
        description: 'Graduates exhibit competence and excellence in their professional practice, continuously striving for high standards of performance.',
        missionKeywordAlignment: ['A', 'C', 'D', 'E']
    },
    {
        id: 'GA8',
        section: 'Competence',
        description: 'Graduates embrace lifelong learning, engage in reflective practice, and contribute to research and innovation for societal advancement.',
        missionKeywordAlignment: ['A', 'C', 'D']
    },
    {
        id: 'GA9',
        section: 'Commitment to Service',
        description: 'Graduates actively contribute to nation-building by engaging in meaningful service and leadership roles in their communities.',
        missionKeywordAlignment: ['A', 'B', 'C', 'D', 'E', 'F']
    },
    {
        id: 'GA10',
        section: 'Commitment to Service',
        description: 'Graduates advocate for environmental sustainability, integrating ecological consciousness into their decisions and actions.',
        missionKeywordAlignment: ['C', 'F']
    },
    {
        id: 'GA11',
        section: 'Commitment to Service',
        description: 'Graduates collaborate effectively in diverse teams, demonstrating commitment, adaptability and teamwork in achieving shared goals.',
        missionKeywordAlignment: ['A', 'B', 'E']
    }
];

let peoRows = [
    {
        id: 'PEO-1',
        description: 'Technical Mastery and Innovation: Graduates will demonstrate strong technical competence and creative problem-solving skills in designing, implementing, and managing IT systems that address real-world challenges in organizations and communities.',
        graduateAttributeAlignment: ['GA5', 'GA6', 'GA7', 'GA8']
    },
    {
        id: 'PEO-2',
        description: 'Professionalism, Leadership, and Ethics: Graduates will exemplify ethical leadership, professionalism, and collaborative engagement in multidisciplinary IT projects, ensuring adherence to legal, social, and organizational standards.',
        graduateAttributeAlignment: ['GA1', 'GA2', 'GA3', 'GA4', 'GA5', 'GA9', 'GA10', 'GA11']
    },
    {
        id: 'PEO-3',
        description: 'Lifelong Learning and Global Adaptability: Graduates will pursue lifelong learning and continuous skill enhancement to remain responsive to evolving technologies, industry demands, and global IT trends.',
        graduateAttributeAlignment: ['GA6', 'GA7', 'GA8', 'GA9', 'GA10', 'GA11']
    },
    {
        id: 'PEO-4',
        description: 'Societal Contribution and Sustainable Development: Graduates will contribute to inclusive and sustainable digital transformation by developing IT solutions that address societal, environmental, and organizational needs across diverse sectors.',
        graduateAttributeAlignment: ['GA1', 'GA2', 'GA3', 'GA4', 'GA5', 'GA6', 'GA7', 'GA8', 'GA9', 'GA10', 'GA11']
    }
];

let ploRows = [
    {
        id: 'PLO-1',
        description: 'Computing Knowledge and Problem Solving: Apply knowledge of computing, science, and mathematics to analyze, design, and solve complex IT problems in various domains.',
        peoAlignment: ['PEO-1']
    },
    {
        id: 'PLO-2',
        description: 'IT Systems Design and Integration: Design, implement, and optimize IT-based solutions that meet user requirements, industry standards, and sustainability goals.',
        peoAlignment: ['PEO-1', 'PEO-2', 'PEO-3']
    },
    {
        id: 'PLO-3',
        description: 'Innovative and Interactive IT Applications: Develop creative, immersive, and user-centered digital systems using advanced tools, emerging technologies, and programming environments.',
        peoAlignment: ['PEO-1', 'PEO-4']
    },
    {
        id: 'PLO-4',
        description: 'Communication and Collaboration: Communicate effectively in oral, written, and digital forms and work productively in diverse teams to deliver quality IT solutions.',
        peoAlignment: ['PEO-2']
    },
    {
        id: 'PLO-5',
        description: 'Ethics, Legal, and Social Responsibility: Uphold ethical, legal, and professional standards in IT practice, ensuring data privacy, security, and inclusivity while addressing organizational and societal challenges.',
        peoAlignment: ['PEO-2']
    },
    {
        id: 'PLO-6',
        description: 'Lifelong Learning and Professional Development: Engage in lifelong learning to stay current with advancements in information technology and to support professional growth.',
        peoAlignment: ['PEO-2', 'PEO-3']
    }
];

const nextGaId = () => {
    const maxId = graduateAttributeRows.reduce((max, row) => {
        const num = Number(String(row.id).replace('GA', ''));
        return Number.isFinite(num) ? Math.max(max, num) : max;
    }, 0);
    return `GA${maxId + 1}`;
};

const nextPeoId = () => {
    const maxId = peoRows.reduce((max, row) => {
        const num = Number(String(row.id).replace('PEO-', ''));
        return Number.isFinite(num) ? Math.max(max, num) : max;
    }, 0);
    return `PEO-${maxId + 1}`;
};

const nextPloId = () => {
    const maxId = ploRows.reduce((max, row) => {
        const num = Number(String(row.id).replace('PLO-', ''));
        return Number.isFinite(num) ? Math.max(max, num) : max;
    }, 0);
    return `PLO-${maxId + 1}`;
};

const renderGraduateAttributesEditor = (container) => {
    const sectionOrder = ['Character', 'Competence', 'Commitment to Service'];
    const rowsHtml = sectionOrder.map((section) => {
        const sectionRows = graduateAttributeRows.filter((row) => row.section === section);
        return `
            <tr class="ga-section-row">
                <th colspan="9" class="d-flex justify-content-between align-items-center">
                    <span>${section.toUpperCase()}</span>
                    <button type="button" class="btn btn-sm btn-outline-success ga-add-btn" data-section="${section}">Add Row</button>
                </th>
            </tr>
            ${sectionRows.map((row) => `
                <tr>
                    <td class="ga-id-cell">${row.id}</td>
                    <td>
                        <textarea class="form-control form-control-sm alignment-text ga-text" rows="2" data-ga-id="${row.id}">${row.description}</textarea>
                    </td>
                    ${missionKeywords.map((keyword) => `
                        <td class="text-center">
                            <input type="checkbox" class="form-check-input ga-mission-checkbox" data-ga-id="${row.id}" data-keyword="${keyword}" ${row.missionKeywordAlignment?.includes(keyword) ? 'checked' : ''}>
                        </td>
                    `).join('')}
                    <td class="text-center">
                        <button type="button" class="btn btn-sm btn-outline-danger ga-remove-btn" data-ga-id="${row.id}">Remove</button>
                    </td>
                </tr>
            `).join('')}
        `;
    }).join('');

    container.innerHTML = `
        <div class="table-responsive">
            <table class="table table-bordered table-sm alignment-input-table mb-0">
                <thead class="table-light">
                    <tr>
                        <th class="ga-id-col">ID</th>
                        <th class="ga-text-col">Graduate Attribute Text</th>
                        ${missionKeywords.map((keyword) => `<th class="text-center keyword-col">${keyword}</th>`).join('')}
                        <th class="action-col text-center">Action</th>
                    </tr>
                </thead>
                <tbody>${rowsHtml}</tbody>
            </table>
        </div>
    `;
};

const renderPeosEditor = (container) => {
    const gaIds = graduateAttributeRows.map((row) => row.id);

    container.innerHTML = `
        <div class="table-responsive">
            <table class="table table-bordered table-sm alignment-input-table mb-0">
                <thead class="table-light">
                    <tr>
                        <th class="peo-id-col">PEO</th>
                        <th class="peo-text-col">Program Educational Objective Text</th>
                        ${gaIds.map((id) => `<th class="text-center align-col">${id}</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${peoRows.map((row) => `
                        <tr>
                            <td class="fw-semibold">${row.id}</td>
                            <td>
                                <textarea class="form-control form-control-sm alignment-text peo-text" rows="3" data-peo-id="${row.id}">${row.description}</textarea>
                            </td>
                            ${gaIds.map((gaId) => `
                                <td class="text-center">
                                    <input type="checkbox" class="form-check-input peo-ga-checkbox" data-peo-id="${row.id}" data-ga-id="${gaId}" ${row.graduateAttributeAlignment?.includes(gaId) ? 'checked' : ''}>
                                </td>
                            `).join('')}
                            <td class="text-center">
                                <button type="button" class="btn btn-sm btn-outline-danger peo-remove-btn" data-peo-id="${row.id}">Remove</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
        <div class="mt-2 text-end">
            <button type="button" class="btn btn-sm btn-outline-warning" id="peoAddBtn">Add PEO</button>
        </div>
    `;
};

const renderPlosEditor = (container) => {
    const peoIds = peoRows.map((row) => row.id);

    container.innerHTML = `
        <div class="table-responsive">
            <table class="table table-bordered table-sm alignment-input-table mb-0">
                <thead class="table-light">
                    <tr>
                        <th class="plo-id-col">PLO</th>
                        <th class="plo-text-col">Program Learning Outcome Text</th>
                        ${peoIds.map((id) => `<th class="text-center align-col">${id}</th>`).join('')}
                        <th class="action-col text-center">Action</th>
                    </tr>
                </thead>
                <tbody>
                    ${ploRows.map((row) => `
                        <tr>
                            <td class="fw-semibold">${row.id}</td>
                            <td>
                                <textarea class="form-control form-control-sm alignment-text plo-text" rows="3" data-plo-id="${row.id}">${row.description}</textarea>
                            </td>
                            ${peoIds.map((peoId) => `
                                <td class="text-center">
                                    <input type="checkbox" class="form-check-input plo-peo-checkbox" data-plo-id="${row.id}" data-peo-id="${peoId}" ${row.peoAlignment?.includes(peoId) ? 'checked' : ''}>
                                </td>
                            `).join('')}
                            <td class="text-center">
                                <button type="button" class="btn btn-sm btn-outline-danger plo-remove-btn" data-plo-id="${row.id}">Remove</button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
        <div class="mt-2 text-end">
            <button type="button" class="btn btn-sm btn-outline-info" id="ploAddBtn">Add PLO</button>
        </div>
    `;
};

const collectGraduateAttributesInput = () => {
    const items = graduateAttributeRows.map((row) => {
        const textEl = document.querySelector(`.ga-text[data-ga-id="${row.id}"]`);
        const checkedKeywords = Array.from(
            document.querySelectorAll(`.ga-mission-checkbox[data-ga-id="${row.id}"]:checked`)
        ).map((checkbox) => checkbox.dataset.keyword);

        return {
            id: row.id,
            section: row.section,
            description: textEl ? textEl.value.trim() : '',
            missionKeywordAlignment: checkedKeywords
        };
    });

    const sections = {
        Character: items.filter((item) => item.section === 'Character').map((item) => item.description).filter(Boolean),
        Competence: items.filter((item) => item.section === 'Competence').map((item) => item.description).filter(Boolean),
        'Commitment to Service': items.filter((item) => item.section === 'Commitment to Service').map((item) => item.description).filter(Boolean)
    };

    return {
        missionKeywords,
        items,
        sections
    };
};

const collectPeosInput = () => {
    return peoRows.map((row) => {
        const textEl = document.querySelector(`.peo-text[data-peo-id="${row.id}"]`);
        const checkedGa = Array.from(
            document.querySelectorAll(`.peo-ga-checkbox[data-peo-id="${row.id}"]:checked`)
        ).map((checkbox) => checkbox.dataset.gaId);

        return {
            id: row.id,
            description: textEl ? textEl.value.trim() : '',
            graduateAttributeAlignment: checkedGa
        };
    }).filter((row) => row.description);
};

const collectPlosInput = () => {
    return ploRows.map((row) => {
        const textEl = document.querySelector(`.plo-text[data-plo-id="${row.id}"]`);
        const checkedPeo = Array.from(
            document.querySelectorAll(`.plo-peo-checkbox[data-plo-id="${row.id}"]:checked`)
        ).map((checkbox) => checkbox.dataset.peoId);

        return {
            id: row.id,
            description: textEl ? textEl.value.trim() : '',
            peoAlignment: checkedPeo
        };
    }).filter((row) => row.description);
};

document.addEventListener('DOMContentLoaded', () => {
    const elements = {
        form: document.getElementById('syllabusForm'),
        generateBtn: document.getElementById('generate'),
        courseTitleInput: document.getElementById('courseTitle'),
        courseCodeInput: document.getElementById('courseCode'),
        durationWeeksInput: document.getElementById('durationWeeks'),
        lectureHoursInput: document.getElementById('lectureHours'),
        labHoursInput: document.getElementById('labHours'),
        topicInput: document.getElementById('topic'),
        gaEditor: document.getElementById('graduateAttributesEditor'),
        peoEditor: document.getElementById('peosEditor'),
        ploEditor: document.getElementById('plosEditor'),
        responseArea: document.getElementById('response')
    };

    renderGraduateAttributesEditor(elements.gaEditor);
    renderPeosEditor(elements.peoEditor);
    renderPlosEditor(elements.ploEditor);

    elements.gaEditor.addEventListener('click', (event) => {
        const addBtn = event.target.closest('.ga-add-btn');
        if (addBtn) {
            const section = addBtn.dataset.section;
            graduateAttributeRows.push({
                id: nextGaId(),
                section,
                description: '',
                missionKeywordAlignment: []
            });
            renderGraduateAttributesEditor(elements.gaEditor);
            renderPeosEditor(elements.peoEditor);
            return;
        }

        const removeBtn = event.target.closest('.ga-remove-btn');
        if (removeBtn) {
            const gaId = removeBtn.dataset.gaId;
            if (graduateAttributeRows.length <= 1) return;
            graduateAttributeRows = graduateAttributeRows.filter((row) => row.id !== gaId);

            // Remove stale GA alignments from PEO rows.
            peoRows = peoRows.map((row) => ({
                ...row,
                graduateAttributeAlignment: (row.graduateAttributeAlignment || []).filter((id) => id !== gaId)
            }));

            renderGraduateAttributesEditor(elements.gaEditor);
            renderPeosEditor(elements.peoEditor);
        }
    });

    elements.peoEditor.addEventListener('click', (event) => {
        const addBtn = event.target.closest('#peoAddBtn');
        if (addBtn) {
            peoRows.push({
                id: nextPeoId(),
                description: '',
                graduateAttributeAlignment: []
            });
            renderPeosEditor(elements.peoEditor);
            renderPlosEditor(elements.ploEditor);
            return;
        }

        const removeBtn = event.target.closest('.peo-remove-btn');
        if (removeBtn) {
            const peoId = removeBtn.dataset.peoId;
            if (peoRows.length <= 1) return;
            peoRows = peoRows.filter((row) => row.id !== peoId);

            // Remove stale PEO alignments from PLO rows.
            ploRows = ploRows.map((row) => ({
                ...row,
                peoAlignment: (row.peoAlignment || []).filter((id) => id !== peoId)
            }));

            renderPeosEditor(elements.peoEditor);
            renderPlosEditor(elements.ploEditor);
        }
    });

    elements.ploEditor.addEventListener('click', (event) => {
        const addBtn = event.target.closest('#ploAddBtn');
        if (addBtn) {
            ploRows.push({
                id: nextPloId(),
                description: '',
                peoAlignment: []
            });
            renderPlosEditor(elements.ploEditor);
            return;
        }

        const removeBtn = event.target.closest('.plo-remove-btn');
        if (removeBtn) {
            const ploId = removeBtn.dataset.ploId;
            if (ploRows.length <= 1) return;
            ploRows = ploRows.filter((row) => row.id !== ploId);
            renderPlosEditor(elements.ploEditor);
        }
    });

    elements.form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const courseTitle = elements.courseTitleInput.value.trim();
        const courseCode = elements.courseCodeInput.value.trim();
        const durationWeeks = Number(elements.durationWeeksInput.value) || 18;
        const lectureHours = Number(elements.lectureHoursInput.value) || 3;
        const labHours = Number(elements.labHoursInput.value) || 2;
        const topic = elements.topicInput.value.trim();

        const graduateAttributesInput = collectGraduateAttributesInput();
        const peosInput = collectPeosInput();
        const plosInput = collectPlosInput();

        if (!courseTitle || !courseCode || !peosInput.length || !plosInput.length) return;

        try {
            elements.generateBtn.disabled = true;
            elements.generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Generating Syllabus...';
            elements.generateBtn.classList.add('disabled');

            elements.responseArea.innerHTML = `
                <div class="d-flex align-items-center justify-content-center p-4">
                    <div class="text-primary">
                        <i class="fas fa-spinner fa-spin fa-2x me-3"></i>
                        Creating your syllabus...
                    </div>
                </div>`;

            const response = await fetch('/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    courseTitle,
                    courseCode,
                    durationWeeks,
                    lectureHours,
                    labHours,
                    topic,
                    graduateAttributesInput,
                    peosInput,
                    plosInput
                })
            });

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            elements.responseArea.innerHTML = renderSyllabus(data.response);
            window.syllabusData = data.response.raw_json;

        } catch (error) {
            console.error('Error:', error);
            elements.responseArea.innerHTML = `
                <div class="alert alert-danger d-flex align-items-center gap-3">
                    <i class="fas fa-exclamation-circle fa-lg"></i>
                    <span>Error generating syllabus: ${error.message}</span>
                </div>`;
        } finally {
            elements.generateBtn.disabled = false;
            elements.generateBtn.innerHTML = '<i class="fas fa-magic me-2"></i>Generate Syllabus';
            elements.generateBtn.classList.remove('disabled');
        }
    });
});
