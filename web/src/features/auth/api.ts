import { getUser, postLogout } from '@shared/api/instance';
import {
  useQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query';


const queryKeys = {
  me: ['user'] as const
}

export const useUser = () => {
  return useQuery({
    queryKey: queryKeys.me,
    queryFn: getUser,
    retry: false,
    staleTime: Infinity,
  });
};

export const useLogout = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: postLogout,
    onError: () => {
      console.error('Logout failed');
    },
    onSuccess: () => {
      queryClient.setQueryData(['user'], null);
      queryClient.invalidateQueries();
    },
  });
};