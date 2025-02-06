import React from 'react';
import { Moon, Sun, Captions, CaptionsOff } from 'lucide-react';
import { useAtom } from 'jotai';
import { viewPrefsAtom } from '@preferences/state';
import { Flex, IconButton } from '@radix-ui/themes';

const ViewOptions: React.FC = () => {
  const [viewPrefs, setViewPrefs] = useAtom(viewPrefsAtom);

  return (
    <Flex gap="2">
      <IconButton
        size="2"
        variant="soft"
        onClick={() => setViewPrefs('hideinfo', !viewPrefs.hideinfo)}
        aria-label={viewPrefs.hideinfo ? 'Show info' : 'Hide info'}
      >
        {viewPrefs.hideinfo ? (
          <CaptionsOff width="16" height="16" />
        ) : (
          <Captions width="16" height="16" />
        )}
      </IconButton>

      <IconButton
        size="2"
        variant="soft"
        onClick={() => setViewPrefs('darkmode', !viewPrefs.darkmode)}
        aria-label={viewPrefs.darkmode ? 'Light mode' : 'Dark mode'}
      >
        {viewPrefs.darkmode ? (
          <Sun width="16" height="16" />
        ) : (
          <Moon width="16" height="16" />
        )}
      </IconButton>
    </Flex>
  );
};

export default ViewOptions