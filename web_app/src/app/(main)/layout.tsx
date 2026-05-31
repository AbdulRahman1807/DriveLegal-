import styles from './main.module.css';

export default function MainLayout({ children }: { children: React.ReactNode }) {
  return <div className={styles.appShell}>{children}</div>;
}
