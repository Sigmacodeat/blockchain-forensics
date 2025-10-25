import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';
import { AddressSearchPanel } from './AddressSearchPanel';

const meta = {
  title: 'Investigator/AddressSearchPanel',
  component: AddressSearchPanel,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    searchQuery: { control: 'text' },
  },
  args: {
    onSearchQueryChange: fn(),
    onSearch: fn(),
  },
} satisfies Meta<typeof AddressSearchPanel>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Empty: Story = {
  args: {
    searchQuery: '',
  },
};

export const WithEthereumAddress: Story = {
  args: {
    searchQuery: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
  },
};

export const WithBitcoinAddress: Story = {
  args: {
    searchQuery: 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh',
  },
};

export const WithInvalidAddress: Story = {
  args: {
    searchQuery: 'invalid_address_123',
  },
};
