# To learn more about how to use Nix to configure your environment
# see: https://firebase.google.com/docs/studio/customize-workspace
{ pkgs, ... }: {
  # Which nixpkgs channel to use.
  channel = "stable-24.05"; # or "unstable"

  # Use https://search.nixos.org/packages to find packages
  packages = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.mariadb # Client tools for MySQL
  ];

  # Sets environment variables in the workspace
  env = {};
  idx = {
    # Search for the extensions you want on https://open-vsx.org/ and use "publisher.id"
    extensions = [
      "ms-python.python"
    ];

    # Enable previews
    previews = {
      enable = false;
      previews = {
        # web = {
        #   command = ["uvicorn" "main:app" "--host" "0.0.0.0" "--port" "$PORT" "--reload"];
        #   manager = "web";
        #   cwd = "Mini-Game-Management-Platform";
        #   env = {
        #     PORT = "$PORT";
        #   };
        # };
      };
    };

    # Workspace lifecycle hooks
    workspace = {
      # Runs when a workspace is first created
      onCreate = {
        install-dependencies = "python -m pip install -r Mini-Game-Management-Platform/requirements.txt";
      };
      # Runs when the workspace is (re)started
      onStart = {
        # Ensure database is running and initialized (simple check)
        # We might need a script to init DB if not exists
      };
    };
  };
  
  services.mysql = {
    enable = true;
    package = pkgs.mariadb;
    # Initial setup if needed, though usually handled via valid SQL init scripts or manually
  };
}
