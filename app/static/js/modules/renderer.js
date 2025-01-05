export const renderSourceLink = (source, title) => {
    let displayTitle = title;
    try {
        const url = new URL(source);
        displayTitle = title || url.hostname;
    } catch (e) {
        displayTitle = title || source;
    }
    return `<a href="${source}" target="_blank" class="source-link" rel="noopener noreferrer">
        <i class="fas fa-external-link-alt"></i> ${displayTitle}
    </a>`;
};

export const renderMetadata = (metadata) => {
    if (!metadata || Object.keys(metadata).length === 0) return '';
    
    let html = '<div class="metadata-section">';
    if (metadata.chunks?.length > 0) {
        html += '<div class="sources-container">';
        html += '<h4>📚 Sources:</h4>';
        html += '<div class="sources-grid">';
        metadata.chunks.forEach(chunk => {
            html += renderSourceLink(chunk.source, chunk.title);
        });
        html += '</div></div>';
    }
    html += '</div>';
    return html;
};

export const configureMarkdown = () => {
    marked.setOptions({
        breaks: true,
        headerIds: true,
        gfm: true,
        smartLists: true,
        smartypants: true
    });
};
