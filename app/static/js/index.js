import { renderSyllabus } from './modules/syllabus.js';

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
        graduateAttributesInput: document.getElementById('graduateAttributesInput'),
        peosInput: document.getElementById('peosInput'),
        plosInput: document.getElementById('plosInput'),
        responseArea: document.getElementById('response')
    };

    elements.form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const courseTitle = elements.courseTitleInput.value.trim();
        const courseCode = elements.courseCodeInput.value.trim();
        const durationWeeks = Number(elements.durationWeeksInput.value) || 18;
        const lectureHours = Number(elements.lectureHoursInput.value) || 3;
        const labHours = Number(elements.labHoursInput.value) || 2;
        const topic = elements.topicInput.value.trim();
        const graduateAttributesInput = elements.graduateAttributesInput.value.trim();
        const peosInput = elements.peosInput.value.trim();
        const plosInput = elements.plosInput.value.trim();

        if (!courseTitle || !courseCode || !graduateAttributesInput || !peosInput || !plosInput) return;

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

            // Render the full university-style syllabus
            elements.responseArea.innerHTML = renderSyllabus(data.response);

            // Store syllabus data globally for potential downstream use
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