export const fetchCandidates = async () => {
  const res = await fetch('/api/v1/candidates/');
  if (!res.ok) throw new Error('Ошибка загрузки кандидатов');
  return res.json();
};

export const fetchVacancies = async () => {
  const res = await fetch('/api/v1/vacancies/');
  if (!res.ok) throw new Error('Ошибка загрузки вакансий');
  return res.json();
};

export const analyzeCandidate = async (candidateId, vacancyId) => {
  const res = await fetch('/api/v1/analyze/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
      candidate_id: parseInt(candidateId), 
      vacancy_id: parseInt(vacancyId) 
    })
  });
  
  if (!res.ok) throw new Error(`Ошибка сервера: ${res.status}`);
  
  const json = await res.json();

  if (!json.success) {
    const errorMsg = json.error?.message || 'Неизвестная ошибка ИИ';
    throw new Error(errorMsg);
  }

  // Бэкенд (и LLM) теперь отдают данные СТРОГО в том формате, 
  // который мы прописали в новом JSON-контракте промпта.
  // Поэтому мы просто возвращаем их как есть!
  return json.data; 
};