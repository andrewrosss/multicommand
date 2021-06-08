import React from "react";
import clsx from "clsx";
import styles from "./HomepageFeatures.module.css";

const FeatureList = [
  {
    title: "Small",
    // Svg: require('../../static/img/undraw_docusaurus_mountain.svg').default,
    description: (
      <>
        The magic happens in a single module (
        <a href="https://github.com/andrewrosss/multicommand/blob/master/src/multicommand.py">
          <code>multicommand.py</code>
        </a>
        )
      </>
    ),
  },
  {
    title: "Simple API",
    // Svg: require('../../static/img/undraw_docusaurus_tree.svg').default,
    description: (
      <>
        Structure commands however you like, then call{" "}
        <code>multicommand.create_parser(...)</code>.
      </>
    ),
  },
  {
    title: "Dependency-Free",
    // Svg: require('../../static/img/undraw_docusaurus_react.svg').default,
    description: (
      <>
        All you need is python 3.6+. <code>multicommand</code> uses just the
        standard library.
      </>
    ),
  },
];

function Feature({ Svg, title, description }) {
  return (
    <div className={clsx("col col--4")}>
      {/* <div className="text--center">
        <Svg className={styles.featureSvg} alt={title} />
      </div> */}
      <div className="text--center padding-horiz--md">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
