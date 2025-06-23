module receiver_logic (
    input wire clk,
    input wire rst,
    input wire push_sender_in_reset,
    input wire [7:0] push_data,
    input wire push_valid,
    input wire pop_credit,
    input wire credit_initial,
    input wire credit_withhold,
    input wire push_credit_stall,
    output reg [7:0] pop_data,
    output reg pop_valid,
    output reg push_credit,
    output reg push_receiver_in_reset
);

    // Internal signals
    reg credit_count;

    always @(posedge clk or posedge rst) begin
        if (rst || push_sender_in_reset) begin
            // Reset behavior
            credit_count <= credit_initial;
            pop_valid <= 0;
            push_credit <= 0;
            push_receiver_in_reset <= 1;
        end else begin
            // Normal operation
            push_receiver_in_reset <= 0;

            if (pop_credit) begin
                // Increment credit count when downstream consumes data
                credit_count <= credit_count + 1;
            end

            if (push_credit_stall == 0 && pop_valid && credit_available != 0) begin
                // Return a credit to the sender
                push_credit <= 1;
            end else begin
                push_credit <= 0;
            end

            if (credit_withhold) begin
                // Withhold a credit
                credit_count <= credit_count - 1;
            end

            pop_valid <= push_valid && !(rst || push_sender_in_reset);
        end
    end

    assign credit_available = credit_count - credit_withhold;

    always @(*) begin
        // Data and validity path
        pop_data = push_data;
    end

endmodule
