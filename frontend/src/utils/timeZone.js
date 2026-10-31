const IST = 'Asia/Kolkata';

export const parseUtcTimestamp = (value) => {
  if (typeof value === 'string' && value && !/(?:Z|[+-]\d{2}:?\d{2})$/i.test(value)) {
    return new Date(`${value}Z`);
  }
  return new Date(value);
};

export const formatIstTime = (value, options) =>
  parseUtcTimestamp(value).toLocaleTimeString('en-IN', { ...options, timeZone: IST });

export const formatIstDateTime = (value, options) =>
  parseUtcTimestamp(value).toLocaleString('en-IN', { ...options, timeZone: IST });
