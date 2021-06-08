/** @type {import('@docusaurus/types').DocusaurusConfig} */
module.exports = {
  title: "Multicommand",
  tagline: "Simple subcommand CLIs with argparse",
  url: "https://your-docusaurus-test-site.com",
  baseUrl: "/",
  onBrokenLinks: "throw",
  onBrokenMarkdownLinks: "warn",
  favicon: "img/favicon.svg",
  organizationName: "andrewrosss", // Usually your GitHub org/user name.
  projectName: "multicommand", // Usually your repo name.
  themeConfig: {
    navbar: {
      title: "Multicommand",
      logo: {
        alt: "Multicommand Logo",
        src: "img/logo.svg",
      },
      items: [
        {
          type: "doc",
          docId: "installation",
          position: "left",
          label: "Docs",
        },
        {
          href: "https://github.com/andrewrosss/multicommand",
          label: "GitHub",
          position: "right",
        },
      ],
    },
    footer: {
      style: "dark",
      links: [
        {
          title: "DOCUMENTATION",
          items: [
            {
              label: "Installation",
              to: "/docs/installation",
            },
            {
              label: "Introduction",
              to: "/docs/introduction",
            },
            {
              label: "Basic Usage",
              to: "/docs/basic-usage",
            },
            {
              label: "Examples",
              to: "/docs/examples/simple",
            },
          ],
        },
        {
          title: "LINKS",
          items: [
            {
              label: "PyPI",
              href: "https://pypi.org/project/multicommand/",
            },
            {
              label: "Github",
              href: "https://github.com/andrewrosss/multicommand",
            },
            {
              label: "Issues",
              href: "https://github.com/andrewrosss/multicommand/issues",
            },
            {
              label: "andrewrosss",
              href: "https://github.com/andrewrosss",
            },
          ],
        },
        {},
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Andrew Ross. Built with Docusaurus.`,
    },
  },
  presets: [
    [
      "@docusaurus/preset-classic",
      {
        docs: {
          sidebarPath: require.resolve("./sidebars.js"),
          // Please change this to your repo.
          editUrl:
            "https://github.com/andrewrosss/multicommand/tree/master/docs",
        },
        theme: {
          customCss: require.resolve("./src/css/custom.css"),
        },
      },
    ],
  ],
};
