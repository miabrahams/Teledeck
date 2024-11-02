import axios, { AxiosResponse } from 'axios';
import { createPreferenceString } from '@shared/api/serialization';
import { API_ENDPOINTS } from './constants';


type ROUTE = typeof API_ENDPOINTS[keyof typeof API_ENDPOINTS];
export const withPreferences = (route: ROUTE, preferences: Parameters<typeof createPreferenceString>[0]) => {
  return `${route}?${createPreferenceString(preferences)}`
}

export const apiHandler = async <T>(
  promise: Promise<AxiosResponse<T>>
): Promise<T> => {
  try {
    const response = await promise;
    return response.data;
  } catch (error) {
    throw normalizeApiError(error);
  }
};


export const apiHandlerOK = async <T>(
  promise: Promise<AxiosResponse<T>>
): Promise<boolean> => {
  try {
    const response = await promise;
    return response.status === 200;
  } catch (error) {
    throw normalizeApiError(error);
  }
};



function normalizeApiError(error: unknown) {
  if (axios.isAxiosError(error)) {
    return {
      message: error.message,
      status: error.response?.status,
      data: error.response?.data,
    };
  }
  return {
    message: 'An unknown error occurred: ' + String(error),
  };
}
