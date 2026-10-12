// Render external dataset values as text inside popup HTML, never as markup.
function escapeHtml(value) {
    const replacements = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
    return String(value ?? '').replace(/[&<>"']/g, character => replacements[character]);
}
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { escapeHtml };
}
