// src/features/navigation/components/SearchBox.tsx
import React, { useState, useEffect } from 'react';
import { Search } from 'lucide-react';
import { useAtom } from 'jotai';
import { searchStringAtom } from '@preferences/state';
import { TextField, Flex } from '@radix-ui/themes';

type SearchBoxProps = {
  fullWidth?: boolean;
};

const SearchBox: React.FC<SearchBoxProps> = ({ fullWidth = false }) => {
  const [searchString, setSearchString] = useAtom(searchStringAtom);
  const [searchValue, setSearchValue] = useState(searchString);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchValue !== searchString) {
        setSearchString(searchValue);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchValue]);

  return (
    <Flex align="center" gap="1" style={{ width: fullWidth ? '100%' : undefined }}>
      <TextField.Root
        size="2"
        placeholder="Search..."
        value={searchValue}
        onChange={(e) => setSearchValue(e.target.value)}
        style={fullWidth ? { width: '100%' } : { minWidth: '200px' }}
      >
        <TextField.Slot>
          <Search width="16" height="16" />
        </TextField.Slot>
      </TextField.Root>
    </Flex>
  );
};

export default SearchBox;