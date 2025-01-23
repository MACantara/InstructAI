export const configureMarkdown = () => {
    const renderer = new marked.Renderer();
    
    renderer.heading = (text, level) => {
        try {
            if (typeof text === 'object' && text.text) {
                text = text.text;
            } else if (typeof text !== 'string') {
                text = String(text || '');
            }
            
            const cleanText = text.replace(/[^\w\s-]/g, '');
            const escapedText = cleanText.toLowerCase().replace(/[^\w]+/g, '-');
            
            if (level === 3 && text.includes('Week')) {
                return `<h${level} id="${escapedText}" class="week-heading">${text}</h${level}>`;
            } else if (level === 4) {
                return `<h${level} id="${escapedText}" class="topic-heading">${text}</h${level}>`;
            }
            
            return `<h${level} id="${escapedText}">${text}</h${level}>`;
        } catch (e) {
            console.warn('Error rendering heading:', e);
            return `<h${level}>Untitled Section</h${level}>`;
        }
    };

    marked.setOptions({
        breaks: true,
        headerIds: true,
        gfm: true,
        smartLists: true,
        smartypants: true,
        headerPrefix: 'section-',
        renderer: renderer
    });
};
