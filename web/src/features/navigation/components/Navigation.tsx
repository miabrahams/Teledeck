// src/features/navigation/components/Navigation.tsx
import React from 'react';
import { Link } from 'react-router-dom';
import ViewOptions from './ViewOptions';
import SearchOptions from './SearchOptions';
import SearchBox from './SearchBox';
import {
  Box,
  Container,
  Flex,
  Button,
  Text,
} from '@radix-ui/themes';
import { User } from '@/shared/types/user';

type NavigationProps = {
  user: User | undefined;
  onLogout: React.MouseEventHandler<HTMLButtonElement>
};

const Navigation: React.FC<NavigationProps> = ({ user, onLogout }) => {

  return (
    <Box
      asChild
      position="sticky"
      top="0"
      style={{
        backgroundColor: 'var(--background-nav)',
        zIndex: 40
      }}
    >
      <nav>
        <Container size="4">
          <Flex justify="between" align="center" py="4" gap="4">
            {/* Left side - Navigation and filters */}
            <Flex align="center" gap="4">
              {/* View Options */}
              <ViewOptions />
              <SearchOptions />
              <SearchBox />
            </Flex>

            {/* Right side - User actions */}
            <Flex align="center" gap="4">
              {user ? (
                <>
                  <Text size="2">Welcome, {user.email}</Text>
                  <Button
                    onClick={onLogout}
                    variant="soft"
                    size="2"
                  >
                    Logout
                  </Button>
                </>
              ) : (
                <>
                  <Link to="/register">
                    <Button variant="soft" size="2">
                      Register
                    </Button>
                  </Link>
                  <Link to="/login">
                    <Button variant="soft" size="2">
                      Login
                    </Button>
                  </Link>
                </>
              )}
            </Flex>
          </Flex>
        </Container>
      </nav>
    </Box>
  );
};

export default Navigation;