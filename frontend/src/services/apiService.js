const API_BASE_URL = 'http://127.0.0.1:8004/api';

export const fetchHealth = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching health data:', error);
    throw error;
  }
};

export const fetchInterfaces = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/interfaces`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching interfaces:', error);
    throw error;
  }
};

export const selectInterface = async (interfaceName) => {
  try {
    const response = await fetch(`${API_BASE_URL}/interfaces/select/${interfaceName}`, {
      method: 'POST'
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error selecting interface:', error);
    throw error;
  }
};

export const deselectInterface = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/interfaces/deselect`, {
      method: 'POST'
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error deselecting interface:', error);
    throw error;
  }
};

export const fetchStats = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/stats/current`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching stats:', error);
    throw error;
  }
};