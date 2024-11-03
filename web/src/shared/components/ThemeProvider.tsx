// src/theme/theme.ts
import { Theme } from '@radix-ui/themes'
import * as RadixColors from '@radix-ui/colors';
import { ThemeProps } from '@radix-ui/themes'
import '@radix-ui/themes/styles.css';

export const myTheme = {
  primary: RadixColors.blue,
  background: RadixColors.slate,
  accent: RadixColors.purple,
};

// Define semantic colors that map to your existing Tailwind primary/dark colors
export const themeConfig: ThemeProps = {
  accentColor: 'blue',
  grayColor: 'slate',
  scaling: '95%',
  appearance: 'dark',
  panelBackground: 'solid',
  radius: 'medium',
} as const;

// Converted to a theme config object
export const themeConfigMint: ThemeProps = {
  accentColor: 'mint',
  grayColor: 'gray',
  scaling: '100%',
  appearance: 'dark',
  panelBackground: 'solid',
  radius: 'full',
} as const;

const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <Theme {...themeConfigMint}>
      {children}
    </Theme>
  );
};


export default ThemeProvider