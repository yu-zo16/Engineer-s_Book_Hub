export const getPeriodRange = (period: string, detail: string) => {
  if (period === 'all') return { start: null, end: null };

  let start: string, end: string;
  if (period === 'monthly') {
    const [year, month] = detail.split('-').map(Number);
    // 月初から翌月の月初まで (ltを使用するため)
    start = `${year}-${String(month).padStart(2, '0')}-01T00:00:00Z`;
    const nextMonth = month === 12 ? 1 : month + 1;
    const nextYear = month === 12 ? year + 1 : year;
    end = `${nextYear}-${String(nextMonth).padStart(2, '0')}-01T00:00:00Z`;
  } else {
    const year = Number(detail);
    start = `${year}-01-01T00:00:00Z`;
    end = `${year + 1}-01-01T00:00:00Z`;
  }

  return { start, end };
};

export const createFilterUrl = (params: any, current: any) => {
  const newParams = new URLSearchParams();
  const combined = { ...current, ...params };
  Object.entries(combined).forEach(([key, value]) => {
    if (value && value !== 'all') newParams.set(key, String(value));
  });
  return `?${newParams.toString()}`;
};