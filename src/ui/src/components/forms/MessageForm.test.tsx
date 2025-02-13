import { NetworkType } from '@/types/api'
import { fireEvent, render, screen } from '@testing-library/react'
import { MessageForm } from './MessageForm'

describe('MessageForm', () => {
    it('renders form elements', () => {
        render(<MessageForm />)

        // Check for form elements
        expect(screen.getByLabelText(/Network Type/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/Destination ID/i)).toBeInTheDocument()
        expect(screen.getByLabelText(/Payload/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /Submit Message/i })).toBeInTheDocument()
    })

    it('handles network type selection', () => {
        render(<MessageForm />)
        const select = screen.getByLabelText(/Network Type/i)

        fireEvent.change(select, { target: { value: NetworkType.ISATDATA_PRO } })
        expect(select).toHaveValue(NetworkType.ISATDATA_PRO.toString())
    })

    it('validates required fields', () => {
        render(<MessageForm />)
        const submitButton = screen.getByRole('button', { name: /Submit Message/i })

        fireEvent.click(submitButton)
        // Form validation should prevent submission without required fields
        expect(screen.getByLabelText(/Destination ID/i)).toBeInvalid()
        expect(screen.getByLabelText(/Payload/i)).toBeInvalid()
    })
}) 