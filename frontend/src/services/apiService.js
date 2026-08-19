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

export const getProtocolStats = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/protocol-analysis/stats`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching protocol stats:', error);
    throw error;
  }
};

export const getTopSourceIPs = async (limit = 10, sortBy = 'bytes') => {
  try {
    const response = await fetch(`${API_BASE_URL}/ip-analysis/stats/source?limit=${limit}&sort_by=${sortBy}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching top source IPs:', error);
    throw error;
  }
};

export const getTopDestinationIPs = async (limit = 10, sortBy = 'bytes') => {
  try {
    const response = await fetch(`${API_BASE_URL}/ip-analysis/stats/destination?limit=${limit}&sort_by=${sortBy}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching top destination IPs:', error);
    throw error;
  }
};

export const getTopSourcePorts = async (limit = 10, sortBy = 'bytes') => {
  try {
    const response = await fetch(`${API_BASE_URL}/port-analysis/stats/source?limit=${limit}&sort_by=${sortBy}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching top source ports:', error);
    throw error;
  }
};

export const getTopDestinationPorts = async (limit = 10, sortBy = 'bytes') => {
  try {
    const response = await fetch(`${API_BASE_URL}/port-analysis/stats/destination?limit=${limit}&sort_by=${sortBy}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching top destination ports:', error);
    throw error;
  }
};

export const getHistory = async (limit = 100, startTime = null, endTime = null) => {
  try {
    let url = `${API_BASE_URL}/history?limit=${limit}`;
    if (startTime) {
      url += `&start_time=${encodeURIComponent(startTime)}`;
    }
    if (endTime) {
      url += `&end_time=${encodeURIComponent(endTime)}`;
    }
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching history:', error);
    throw error;
  }
};

export const getLatestHistory = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/history/latest`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching latest history:', error);
    throw error;
  }
};

export const clearHistory = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/history`, {
      method: 'DELETE'
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error clearing history:', error);
    throw error;
  }
};