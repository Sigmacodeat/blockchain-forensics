import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { AddressSearchPanel } from '../AddressSearchPanel';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue: string) => defaultValue,
  }),
}));

describe('AddressSearchPanel', () => {
  it('renders search input and button', () => {
    render(
      <AddressSearchPanel
        searchQuery=""
        onSearchQueryChange={vi.fn()}
        onSearch={vi.fn()}
      />
    );
    
    expect(screen.getByPlaceholderText('Enter address (0x... or bc1...)')).toBeInTheDocument();
    expect(screen.getByText('Explore Address')).toBeInTheDocument();
  });

  it('calls onSearchQueryChange when typing', () => {
    const mockOnChange = vi.fn();
    render(
      <AddressSearchPanel
        searchQuery=""
        onSearchQueryChange={mockOnChange}
        onSearch={vi.fn()}
      />
    );
    
    const input = screen.getByPlaceholderText('Enter address (0x... or bc1...)');
    fireEvent.change(input, { target: { value: '0xabc123' } });
    
    expect(mockOnChange).toHaveBeenCalledWith('0xabc123');
  });

  it('calls onSearch when clicking button', () => {
    const mockOnSearch = vi.fn();
    render(
      <AddressSearchPanel
        searchQuery="0xabc123"
        onSearchQueryChange={vi.fn()}
        onSearch={mockOnSearch}
      />
    );
    
    const button = screen.getByText('Explore Address');
    fireEvent.click(button);
    
    expect(mockOnSearch).toHaveBeenCalledTimes(1);
  });

  it('calls onSearch when pressing Enter', () => {
    const mockOnSearch = vi.fn();
    render(
      <AddressSearchPanel
        searchQuery="0xabc123"
        onSearchQueryChange={vi.fn()}
        onSearch={mockOnSearch}
      />
    );
    
    const input = screen.getByPlaceholderText('Enter address (0x... or bc1...)');
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13 });
    
    expect(mockOnSearch).toHaveBeenCalledTimes(1);
  });

  it('displays current search query', () => {
    render(
      <AddressSearchPanel
        searchQuery="0xabc123def456"
        onSearchQueryChange={vi.fn()}
        onSearch={vi.fn()}
      />
    );
    
    const input = screen.getByPlaceholderText('Enter address (0x... or bc1...)') as HTMLInputElement;
    expect(input.value).toBe('0xabc123def456');
  });
});
