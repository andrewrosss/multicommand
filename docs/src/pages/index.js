import HomepageFeatures from "../components/HomepageFeatures";
import Layout from "@theme/Layout";
import Link from "@docusaurus/Link";
import React from "react";
import clsx from "clsx";
import styles from "./index.module.css";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";

function HomepageHeader() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <header
      className={clsx(
        "hero hero--primary",
        styles.heroBanner,
        styles.heroBackground
      )}
    >
      <div className="container">
        <img
          src="/img/logo.svg"
          className={clsx("shadow--lw", styles.heroImage)}
        />
        <h1 className="hero__title">{siteConfig.title}</h1>
        <p className="hero__subtitle">{siteConfig.tagline}</p>
        <div className={styles.buttons}>
          <Link
            className="button button--outline button--secondary button--lg"
            to="/docs/basic-usage"
          >
            Tutorial
          </Link>
          <Link
            className="button button--secondary button--lg"
            to="/docs/installation"
          >
            Install
          </Link>
        </div>
      </div>
    </header>
  );
}

export default function Home() {
  const { siteConfig } = useDocusaurusContext();
  return (
    <Layout
      title={`${siteConfig.title}`}
      description="Simple subcommand CLIs with argparse"
    >
      <HomepageHeader />
      <main>
        <HomepageFeatures />
      </main>
    </Layout>
  );
}
