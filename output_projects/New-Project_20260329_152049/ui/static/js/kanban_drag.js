document.addEventListener('DOMContentLoaded', () => {
  const columns = document.querySelectorAll('.kanban-column');
  const cards   = document.querySelectorAll('.kanban-card');

  cards.forEach(card => {
    card.draggable = true;

    card.addEventListener('dragstart', e => {
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/html', card.outerHTML);
      e.dataTransfer.setData('card-id', card.dataset.ticketId);
      card.classList.add('dragging');
    });

    card.addEventListener('dragend', () => {
      card.classList.remove('dragging');
    });
  });

  columns.forEach(col => {
    col.addEventListener('dragover', e => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      const dragging = document.querySelector('.dragging');
      if (!dragging) return;
      const afterElement = getDragAfterElement(col, e.clientY);
      if (afterElement == null) {
        col.querySelector('.kanban-cards').appendChild(dragging);
      } else {
        col.querySelector('.kanban-cards').insertBefore(dragging, afterElement);
      }
    });

    col.addEventListener('drop', e => {
      e.preventDefault();
      const ticketId = e.dataTransfer.getData('card-id');
      const newStatus = col.dataset.status;
      fetch(`/api/ticket/${ticketId}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      })
      .then(r => r.json())
      .then(data => {
        if (!data.ok) alert('更新狀態失敗');
      });
    });
  });

  function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.kanban-card:not(.dragging)')];
    return draggableElements.reduce((closest, child) => {
      const box = child.getBoundingClientRect();
      const offset = y - box.top - box.height / 2;
      if (offset < 0 && offset > closest.offset) {
        return { offset: offset, element: child };
      } else {
        return closest;
      }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
  }
});