import { renderSyllabus } from './modules/syllabus.js';

document.addEventListener('DOMContentLoaded', () => {
    const elements = {
        form: document.getElementById('syllabusForm'),
        generateBtn: document.getElementById('generate'),
        topicInput: document.getElementById('topic'),
        responseArea: document.getElementById('response')
    };

    elements.form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const topic = elements.topicInput.value.trim();
        if (!topic) return;

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
                    topic: topic
                })
            });

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Render syllabus as a table
            const weeks = data.response.raw_json.weeklyTopics;
            elements.responseArea.innerHTML = `
                <div class="card shadow-sm">
                    <div class="card-header bg-white">
                        <h2 class="h5 mb-0"><i class="fas fa-table me-2 text-primary"></i>${data.response.raw_json.title}</h2>
                    </div>
                    <div class="table-responsive">
                        <table class="table table-hover table-bordered align-middle mb-0">
                            <thead class="table-light">
                                <tr>
                                    <th scope="col" style="width:70px;">Week</th>
                                    <th scope="col">Main Topic</th>
                                    <th scope="col">Description</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${weeks.map(week => `
                                    <tr>
                                        <td class="text-center fw-bold">${week.week}</td>
                                        <td class="fw-semibold">${week.mainTopic}</td>
                                        <td class="text-secondary small">${week.description || ''}</td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>`;

            // Store syllabus data globally
            window.syllabusData = data.response.raw_json;
            
        } catch (error) {
            console.error('Error:', error);
            elements.responseArea.innerHTML = `
                <div class="alert alert-danger d-flex align-items-center gap-3">
                    <i class="fas fa-exclamation-circle"></i>
                    <span>Error generating syllabus: ${error.message}</span>
                </div>`;
        } finally {
            elements.generateBtn.disabled = false;
            elements.generateBtn.innerHTML = 'Generate Syllabus';
            elements.generateBtn.classList.remove('disabled');
        }
    });
});