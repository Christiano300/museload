{ pkgs ? import <nixpkgs> {} }:
  pkgs.mkShell {
    nativeBuildInputs = with pkgs; [
      playwright-driver.browsers
      python312Packages.playwright
      python312Packages.pypdf
      python312Packages.svglib
      python312Packages.tqdm
      playwright
    ];

    shellHook = ''
      export PLAYWRIGHT_BROWSERS_PATH=${pkgs.playwright-driver.browsers}
      export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=true
    '';
}