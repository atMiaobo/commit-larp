{ pkgs ? import <nixpkgs> { } }:
pkgs.writeShellApplication {
  name = "gitlarp";
  runtimeInputs = [ pkgs.git pkgs.coreutils ];
  text = builtins.readFile ./gitlarp;
}
