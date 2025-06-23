module counter (
  input wire clk,
  input wire incr_valid,
  input [1:0] incr,
  input wire decr_valid,
  input [1:0] decr,
  input wire reinit,
  input wire rst,
  output reg [3:0] value,
  output reg [3:0] value_next
);

  // Initial value for the counter
  parameter initial_value = 4'b0000;

  always_ff @(posedge clk) begin
    if (rst)
      value <= initial_value;
    else if (reinit)
      value <= initial_value;
    else if (incr_valid && incr != 3'b000) // Valid increment amount
      case (incr)
        2'b01: value <= value + 1;
        2'b10: value <= value + 2;
        default: ; // No change for invalid or zero increment
      endcase
    else if (decr_valid && decr != 3'b000) // Valid decrement amount
      case (decr)
        2'b01: value <= value - 1;
        2'b10: value <= value - 2;
        default: ; // No change for invalid or zero decrement
      endcase
  end

  assign value_next = value;

endmodule
