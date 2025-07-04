module ecc_sed_encoder(clk, rst, data_valid, enc_valid, data, enc_codeword);
  wire _05_;
  wire _06_;
  wire _07_;
  wire _08_;
  wire _00_;
  wire _01_;
  wire _02_;
  wire _03_;
  wire _04_;
  input clk;
  wire clk;
  input [11:0] data;
  wire [11:0] data;
  input data_valid;
  wire data_valid;
  output [12:0] enc_codeword;
  wire [12:0] enc_codeword;
  output enc_valid;
  wire enc_valid;
  wire parity;
  input rst;
  wire rst;
  assign _05_ = data[5] ^ _02_;
  assign _03_ = ~ _05_;
  assign _06_ = _01_ ^ _03_;
  assign _04_ = ~ _06_;
  assign _07_ = _04_ ^ 1'h1;
  assign parity = ~ _07_;
  assign _00_ = data[1] ^ data[2];
  assign _08_ = data[0] ^ _00_;
  assign _01_ = ~ _08_;
  assign _02_ = data[3] ^ data[4];
  assign enc_codeword = { parity, data };
  assign enc_valid = data_valid;
endmodule
