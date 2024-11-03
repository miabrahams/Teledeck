
// src/features/navigation/components/SearchOptions.tsx
import React from 'react';
import { useAtom } from 'jotai';
import { searchPrefsAtom } from '@preferences/state';
import { favoriteOptions, sortOptions } from '../constants';
import { Select, Flex, Text, Checkbox } from '@radix-ui/themes';

const SearchOptions: React.FC = () => {
  const [searchPrefs, setSearchPrefs] = useAtom(searchPrefsAtom);

  return (
    <Flex align="center" gap="4">
      <Select.Root
        value={searchPrefs.sort}
        onValueChange={(value) => setSearchPrefs('sort', value)}
      >
        <Select.Trigger />
        <Select.Content>
          {Object.entries(sortOptions).map(([value, label]) => (
            <Select.Item key={value} value={value}>
              {label}
            </Select.Item>
          ))}
        </Select.Content>
      </Select.Root>

      <Select.Root
        value={searchPrefs.favorites}
        onValueChange={(value) => setSearchPrefs('favorites', value)}
      >
        <Select.Trigger />
        <Select.Content>
          {Object.entries(favoriteOptions).map(([value, label]) => (
            <Select.Item key={value} value={value}>
              {label}
            </Select.Item>
          ))}
        </Select.Content>
      </Select.Root>

      <Flex align="center" gap="2">
        <Checkbox
          id="videos-only"
          checked={searchPrefs.videos}
          onCheckedChange={(checked) =>
            setSearchPrefs('videos', checked === true)
          }
        />
        <Text asChild size="2">
          <label htmlFor="videos-only">
            Videos only
          </label>
        </Text>
      </Flex>
    </Flex>
  );
};

export default SearchOptions;