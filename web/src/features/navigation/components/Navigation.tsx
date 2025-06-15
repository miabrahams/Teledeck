// src/features/navigation/components/Navigation.tsx
import React, { useState } from 'react';
import { Link } from '@tanstack/react-router';
import ViewOptions from './ViewOptions';
import SearchOptions from './SearchOptions';
import SearchBox from './SearchBox';
import { Menu } from 'lucide-react';
import {
  Box,
  Container,
  Flex,
  Button,
  Text,
  IconButton,
} from '@radix-ui/themes';
import { User } from '@/shared/types/user';

type NavigationProps = {
  user: User | undefined;
  onLogout: React.MouseEventHandler<HTMLButtonElement>
};

const Navigation: React.FC<NavigationProps> = ({ user, onLogout }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <Box
      asChild
      position="sticky"
      top="0"
      style={{
        backgroundColor: 'var(--background-nav)',
        zIndex: 40,
      }}
    >
      <nav>
        <Container size="4">
          {/* Desktop Layout */}
          <Flex
            display={{ initial: 'none', md: 'flex' }}
            justify="between"
            align="center"
            py="4"
            gap="4"
          >
            {/* Left side - Navigation and filters */}
            <Flex align="center" gap="4">
              <Link to="/">
                <Text color="gray" weight="medium" size="2" highContrast>
                  Home
                </Text>
              </Link>
              <Link to="/about">
                <Text color="gray" weight="medium" size="2" highContrast>
                  About
                </Text>
              </Link>

              <ViewOptions />
              <Flex align="center" gap="4">
                <SearchOptions />
              </Flex>
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

          {/* Mobile Layout */}
          <Flex
            direction="row"
            wrap="wrap"
            display={{ initial: 'flex', md: 'none' }}
          >
            <Flex justify="between" align="center" py="2">
              <SearchBox />
              <IconButton
                variant="ghost"
                onClick={() => setIsMenuOpen(!isMenuOpen)}
              >
                <Menu />
              </IconButton>
            </Flex>

            {isMenuOpen && (
              <Flex direction="row" wrap="wrap" gap="2" py="2">
                <ViewOptions />
                <SearchOptions />
                {/* user ? (
                  <>
                    <Text size="2">Welcome, {user.email}</Text>
                    <Button onClick={onLogout} variant="soft" size="2">
                      Logout
                    </Button>
                  </>
                ) : (
                  <>
                    <Link to="/register">
                      <Button variant="soft" size="2" width="100%">
                        Register
                      </Button>
                    </Link>
                    <Link to="/login">
                      <Button variant="soft" size="2" width="100%">
                        Login
                      </Button>
                    </Link>
                  </>
                )*/}
              </Flex>
            )}
          </Flex>
        </Container>
      </nav>
    </Box>
  );
};

export default Navigation;